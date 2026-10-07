"""프롬프트 관리 프로그램 (2단계 1-1, Python · Git 기초)

대학교 에너지인력양성센터에서 쓰는 프롬프트를 콘솔 메뉴로 관리한다.
기본 데이터는 이전 미션(B1 정리봇, B3 문의 자동화)에서 작성한 프롬프트다.
"""

import json
import os

# 보너스 1: 저장 파일과 내보내기 폴더
DATA_FILE = "prompts.json"
EXPORT_DIR = "prompts_export"

# 미리 정의된 카테고리 (추가 시 번호로 선택하거나 직접 입력)
CATEGORIES = ["텍스트 생성", "이미지 생성", "영상 생성", "페르소나", "자동화", "기타"]

# 프롬프트 데이터: 리스트 안에 딕셔너리 (title / content / category / favorite)
PROMPTS = [
    {
        "title": "정리봇 v1 — 회의록 요약 (B1)",
        "content": (
            "너는 대학교 에너지인력양성센터의 회의록 정리 비서야.\n"
            "아래 회의 내용을 요약해줘."
        ),
        "category": "텍스트 생성",
        "favorite": False,
    },
    {
        "title": "정리봇 v2.1 — 시스템 프롬프트 (B1 최종)",
        "content": (
            "[역할] 너는 \"정리봇\", 대학교 에너지인력양성센터의 행정 경력 10년차 "
            "회의록 정리 전문 비서다.\n"
            "[목표] 회의 메모를 받아 센터 내부 공유용 요약을 작성한다. "
            "담당자가 그대로 복사해 팀에 공유할 수 있는 수준이어야 한다.\n"
            "[말투] 간결한 존댓말, 불릿 중심. 인사말·이모지·마무리 제안 금지. "
            "인물은 실명 대신 역할명만 사용한다.\n"
            "[작업 순서] 출력 항목 기준으로 원문을 한 줄씩 검토 → 확정/예정/미확정 구분 → "
            "정보가 부족하면 최대 3개까지 확인 질문 → 답을 받은 뒤 요약한다.\n"
            "[출력 형식]\n"
            "■ 결정사항: 확정된 것만\n"
            "■ Action Items: 담당 역할명 / 할 일 / 기한 (없으면 \"확인 필요\")\n"
            "■ 리스크: 원문에서 확인되는 지연·누락 가능성\n"
            "■ 후속 일정: 날짜·시간이 명시된 것만, \"예정\"은 \"예정\"으로\n"
            "■ 확인 필요: 근거가 없거나 미확정인 것\n"
            "끝에 \"핵심 근거\" 불릿 3개를 덧붙인다.\n"
            "[규칙] 원문에 없는 내용은 추가하지 않는다. 추측성 표현을 쓰지 않는다. "
            "\"예정\"을 \"확정\"으로 바꾸지 않는다. 발언자를 담당자로 쓰지 않는다. "
            "공유일·회의일은 제작 기한이 아니다."
        ),
        "category": "페르소나",
        "favorite": True,
    },
    {
        "title": "회의록 공통 입력 템플릿 (B1)",
        "content": (
            "[업무 과업] 회의록 요약\n"
            "[원문] (회의 메모 붙여넣기)\n"
            "[원하는 결과] 결정사항 / Action Items / 리스크 / 후속 일정 / 확인 필요\n"
            "[톤] 간결, 센터 내부 공유용\n"
            "[금지] 추측성 표현 금지, 인물 실명 대신 역할명 사용\n"
            "[확인 질문 규칙] 정보가 부족하면 최대 3개까지 질문 후 요약 시작"
        ),
        "category": "텍스트 생성",
        "favorite": False,
    },
    {
        "title": "담당자 알림 메일 템플릿 — 문의 유형별 (B3)",
        "content": (
            "To: {{문의 유형}} 담당자 (프로그램 / 학생인건비 / 기타 → 센터 총괄)\n"
            "Subject: [{{문의 유형}}] {{이름}}님의 문의가 접수되었습니다\n"
            "Content: 문의자: {{이름}} / 이메일: {{이메일}} / 내용: {{문의 내용}}\n"
            "※ {{ }}는 Google Forms 응답 변수. Make Router 경로별로 받는 사람만 바뀐다."
        ),
        "category": "자동화",
        "favorite": False,
    },
    {
        "title": "학생 접수 확인 메일 템플릿 (B3)",
        "content": (
            "To: {{이메일}}\n"
            "Subject: [에너지인력양성센터] 문의가 접수되었습니다\n"
            "Content:\n"
            "{{이름}}님 안녕하세요.\n"
            "에너지인력양성센터에 보내주신 문의가 정상적으로 접수되었습니다.\n"
            "■ 문의 유형: {{문의 유형}}\n"
            "■ 문의 내용: {{문의 내용}}\n"
            "담당자 확인 후 빠른 시일 내에 답변 드리겠습니다.\n"
            "감사합니다."
        ),
        "category": "자동화",
        "favorite": True,
    },
]


# ---------- 공통 헬퍼 ----------

def input_required(label):
    """빈 값이면 다시 입력을 요청한다."""
    while True:
        value = input(label).strip()
        if value:
            return value
        print("비어 있습니다. 다시 입력하세요.")


def input_number(label, max_n):
    """1~max_n 범위의 번호를 입력받아 0부터 시작하는 인덱스로 돌려준다. 잘못되면 None."""
    choice = input(label).strip()
    if choice.isdigit() and 1 <= int(choice) <= max_n:
        return int(choice) - 1
    print(f"잘못된 번호입니다. 1~{max_n} 사이의 번호를 입력하세요.")
    return None


def star(p):
    """즐겨찾기면 ' ⭐', 아니면 빈 문자열."""
    return " ⭐" if p["favorite"] else ""


def print_prompt_line(number, p, with_category=True):
    """목록 한 줄 출력: '번호. [카테고리] 제목 ⭐'"""
    category = f"[{p['category']}] " if with_category else ""
    print(f"{number}. {category}{p['title']}{star(p)}")


def print_categories():
    """카테고리 목록을 '1) 이름' 형식으로 출력한다."""
    for i, name in enumerate(CATEGORIES, start=1):
        print(f"{i}) {name}")


def select_category(allow_custom=False):
    """카테고리를 번호로 고르게 한다. allow_custom이면 직접 입력 항목을 추가한다."""
    print_categories()
    custom_no = len(CATEGORIES) + 1
    if allow_custom:
        print(f"{custom_no}) 직접 입력")
    while True:
        choice = input("선택: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]
        if allow_custom and choice == str(custom_no):
            return input_required("카테고리 이름: ")
        if not allow_custom:
            return None
        print("잘못된 번호입니다. 다시 선택하세요.")


# ---------- 기능 ----------

def add_prompt():
    """제목·내용·카테고리를 입력받아 새 프롬프트를 리스트에 추가한다."""
    print()
    print("=== 프롬프트 추가 ===")
    title = input_required("제목: ")
    content = input_required("내용: ")
    print()
    print("카테고리 선택:")
    category = select_category(allow_custom=True)
    PROMPTS.append({
        "title": title,
        "content": content,
        "category": category,
        "favorite": False,
    })
    print()
    print(f"'{title}' 프롬프트가 추가되었습니다! (현재 {len(PROMPTS)}개)")


def show_list():
    """저장된 모든 프롬프트를 번호·카테고리·제목·즐겨찾기(⭐)와 함께 출력한다."""
    print()
    print("=== 프롬프트 목록 ===")
    if not PROMPTS:
        print("등록된 프롬프트가 없습니다. 1번 메뉴에서 추가하세요.")
        return
    for i, p in enumerate(PROMPTS, start=1):
        print_prompt_line(i, p)
    print()
    print(f"총 {len(PROMPTS)}개의 프롬프트")


def show_by_category():
    """카테고리를 선택하면 그 카테고리의 프롬프트만 출력한다."""
    print()
    print("=== 카테고리별 조회 ===")
    category = select_category()
    if category is None:
        print("잘못된 번호입니다.")
        return
    found = [p for p in PROMPTS if p["category"] == category]
    print()
    print(f"[{category}] 카테고리 프롬프트:")
    if not found:
        print("이 카테고리에는 프롬프트가 없습니다.")
        return
    for i, p in enumerate(found, start=1):
        print_prompt_line(i, p, with_category=False)
    print()
    print(f"총 {len(found)}개의 프롬프트")


def search_prompt():
    """키워드가 제목 또는 내용에 포함된 프롬프트를 대소문자 구분 없이 찾는다."""
    print()
    print("=== 프롬프트 검색 ===")
    keyword = input("검색어: ").strip().lower()
    if not keyword:
        print("검색어가 비어 있습니다.")
        return
    found = [
        (i, p) for i, p in enumerate(PROMPTS, start=1)
        if keyword in p["title"].lower() or keyword in p["content"].lower()
    ]
    print()
    if not found:
        print(f"'{keyword}'이(가) 포함된 프롬프트가 없습니다.")
        return
    print("검색 결과:")
    for i, p in found:
        print_prompt_line(i, p)
    print(f"{len(found)}개의 프롬프트를 찾았습니다.")


def show_detail():
    """번호를 입력받아 프롬프트의 전체 내용을 출력한다."""
    print()
    print("=== 프롬프트 상세 보기 ===")
    index = input_number("번호 입력: ", len(PROMPTS))
    if index is None:
        return
    p = PROMPTS[index]
    line = "―" * 24
    print()
    print(line)
    print(f"제목: {p['title']}")
    print(f"카테고리: {p['category']}")
    print(f"즐겨찾기: {'⭐' if p['favorite'] else '없음'}")
    print(line)
    print("내용:")
    print(p["content"])
    print(line)


def toggle_favorite():
    """번호를 입력받아 즐겨찾기를 추가하거나 해제한다."""
    print()
    print("=== 즐겨찾기 추가/해제 ===")
    index = input_number("프롬프트 번호 입력: ", len(PROMPTS))
    if index is None:
        return
    p = PROMPTS[index]
    p["favorite"] = not p["favorite"]
    if p["favorite"]:
        print(f"'{p['title']}' 프롬프트를 즐겨찾기에 추가했습니다!")
    else:
        print(f"'{p['title']}' 프롬프트를 즐겨찾기에서 해제했습니다.")


def show_favorites():
    """즐겨찾기된 프롬프트만 모아서 출력한다."""
    print()
    print("=== 즐겨찾기 목록 ===")
    found = [(i, p) for i, p in enumerate(PROMPTS, start=1) if p["favorite"]]
    if not found:
        print("즐겨찾기한 프롬프트가 없습니다. 6번 메뉴에서 추가하세요.")
        return
    for i, p in found:
        print_prompt_line(i, p)
    print()
    print(f"총 {len(found)}개의 즐겨찾기")


# ---------- 보너스 1: 영속화·내보내기 ----------

def save_json():
    """프롬프트 전체를 JSON 파일로 저장한다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(PROMPTS, f, ensure_ascii=False, indent=2)
    print(f"{len(PROMPTS)}개의 프롬프트를 '{DATA_FILE}'에 저장했습니다.")


def load_json(quiet=False):
    """JSON 파일을 읽어 프롬프트 리스트를 교체한다. 파일이 없거나 형식이 잘못되면 안내한다."""
    if not os.path.exists(DATA_FILE):
        if not quiet:
            print(f"'{DATA_FILE}' 파일이 없습니다. 먼저 저장하세요.")
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"'{DATA_FILE}'을 읽지 못했습니다: {e}")
        return
    if not isinstance(data, list):
        print(f"'{DATA_FILE}' 형식이 잘못되었습니다. (리스트가 아님)")
        return
    loaded = []
    for item in data:
        if not isinstance(item, dict) or "title" not in item or "content" not in item:
            continue
        loaded.append({
            "title": str(item["title"]),
            "content": str(item["content"]),
            "category": str(item.get("category", "기타")),
            "favorite": bool(item.get("favorite", False)),
        })
    PROMPTS[:] = loaded
    print(f"'{DATA_FILE}'에서 {len(PROMPTS)}개의 프롬프트를 불러왔습니다.")


# ---------- 메뉴 ----------

MENU = [
    ("1", "프롬프트 추가", add_prompt),
    ("2", "프롬프트 목록", show_list),
    ("3", "카테고리별 조회", show_by_category),
    ("4", "프롬프트 검색", search_prompt),
    ("5", "프롬프트 상세 보기", show_detail),
    ("6", "즐겨찾기 추가/해제", toggle_favorite),
    ("7", "즐겨찾기 목록", show_favorites),
    ("8", "JSON 저장", save_json),
    ("9", "JSON 불러오기", load_json),
]


def show_menu():
    """메뉴를 출력한다."""
    print()
    print("=== 프롬프트 관리 프로그램 (에너지인력양성센터) ===")
    for number, name, _ in MENU:
        print(f"{number}. {name}")
    print("0. 종료")


def main():
    """메뉴를 반복 출력하고 번호에 맞는 기능을 실행한다."""
    actions = {number: func for number, _, func in MENU}
    load_json(quiet=True)  # 저장 파일이 있으면 시작할 때 불러온다
    while True:
        show_menu()
        choice = input("선택: ").strip()
        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        if choice in actions:
            actions[choice]()
        else:
            print("잘못된 번호입니다. 메뉴에 있는 번호를 입력하세요.")


if __name__ == "__main__":
    main()
