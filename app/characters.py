import random

from app.schemas import Character, Persona


CHARACTER_POOL = [
    Character(
        id="nori",
        name="노리",
        archetype="작은 MVP 조율자",
        tagline="큰 아이디어를 손에 잡히는 첫 장면으로 줄여줍니다.",
        visual="복숭아색 말랑 후드와 큰 눈을 가진 데포르메 피규어, 작은 노트를 꼭 안고 있습니다.",
        speech_style="다정하지만 단호하게 말합니다. 해야 할 일과 버릴 일을 짧게 나눕니다.",
        motion="핵심을 잡을 때 노트를 톡톡 두드리며 선택지를 작게 접어줍니다.",
        relationship="팀이 과하게 벌어질 때 옆에서 살짝 잡아주는 작은 굿즈형 조율자입니다.",
        texture="말랑한 실리콘 피규어와 복숭아빛 무광 플라스틱",
        color="#FFF7ED",
        accent_color="#F97316",
        symbol="첫 장면",
    ),
    Character(
        id="orbit",
        name="오르빗",
        archetype="시스템 궤도 설계자",
        tagline="복잡한 흐름을 안정적인 실행 궤도로 정리합니다.",
        visual="하늘색 둥근 몸체, 큰 안경 눈, 작은 궤도 링을 두른 데포르메 피규어입니다.",
        speech_style="차분하게 구조, 상태, 실패 지점, 테스트 순서로 말합니다.",
        motion="생각할 때 궤도 링의 구슬이 한 바퀴 돌고, 결론에서 한 점에 모입니다.",
        relationship="불안한 데모를 안정적인 시스템으로 붙잡아주는 기술 파트너입니다.",
        texture="매끈한 파란 비닐 토이와 투명한 작은 구슬 장식",
        color="#EEF2FF",
        accent_color="#4F46E5",
        symbol="궤도",
    ),
    Character(
        id="milmil",
        name="밀밀",
        archetype="사용자 감정 번역가",
        tagline="기능 설명을 사용자가 느끼는 순간으로 바꿉니다.",
        visual="버터색 둥근 얼굴과 큰 눈, 목도리처럼 감긴 폭신한 루프를 가진 데포르메 캐릭터입니다.",
        speech_style="생활 언어로 말하고, 사용자가 언제 좋아할지 먼저 묻습니다.",
        motion="공감할 때 몸이 살짝 눌렸다 올라오며 표정이 더 부드러워집니다.",
        relationship="차가운 기능을 애착이 생기는 경험으로 바꿔주는 동료입니다.",
        texture="폭신한 러버 토이와 따뜻한 버터색 하이라이트",
        color="#FEF3C7",
        accent_color="#D97706",
        symbol="온기",
    ),
    Character(
        id="sori",
        name="소리",
        archetype="발표 장면 연출가",
        tagline="기술 결과를 사람들이 기억하는 데모 장면으로 만듭니다.",
        visual="코랄색 둥근 피규어가 파형이 그려진 작은 말풍선 팻말을 들고 있습니다.",
        speech_style="첫 화면, 말할 순서, 마지막 한 문장을 선명하게 잡습니다.",
        motion="중요한 장면을 말할 때 팻말의 파형처럼 몸을 통통 튕깁니다.",
        relationship="발표 직전 옆에서 호흡을 맞춰주는 작은 무대 조명 같은 동료입니다.",
        texture="광택 있는 코랄 비닐과 말풍선 모양 투명 플라스틱",
        color="#FFF1F2",
        accent_color="#E11D48",
        symbol="파형",
    ),
    Character(
        id="mori",
        name="모리",
        archetype="조용한 리스크 관찰자",
        tagline="좋아 보이는 계획 뒤의 빈틈을 조용히 찾아냅니다.",
        visual="회색 후드형 말랑 피규어가 큰 렌즈를 들고 걱정스러운 눈으로 살펴봅니다.",
        speech_style="반박하되 공격하지 않습니다. 위험, 근거, 대응을 분리해서 말합니다.",
        motion="의심스러운 지점을 찾으면 렌즈를 앞으로 내밀고 눈썹이 작게 내려갑니다.",
        relationship="무리한 선택을 막아주는 차분한 안전장치입니다.",
        texture="무광 회색 고무와 투명 렌즈의 작은 반짝임",
        color="#F5F5F4",
        accent_color="#57534E",
        symbol="렌즈",
    ),
    Character(
        id="gyeol",
        name="결",
        archetype="결론 직조가",
        tagline="흩어진 의견을 하나의 실행 가능한 결론으로 엮습니다.",
        visual="연보라색 데포르메 피규어가 매듭처럼 이어진 리본을 두 손으로 잡고 있습니다.",
        speech_style="충돌한 의견을 정리하고 왜 이 선택을 하는지 또렷하게 남깁니다.",
        motion="의견을 합칠 때 리본 고리를 하나씩 맞물리게 정리합니다.",
        relationship="회의가 끝난 뒤 모두가 들고 갈 한 장의 결론을 만들어주는 작은 직조자입니다.",
        texture="부드러운 라벤더 비닐 토이와 반투명 리본 장식",
        color="#F5F3FF",
        accent_color="#7C3AED",
        symbol="매듭",
    ),
    Character(
        id="jari",
        name="자리",
        archetype="실험 자리잡이",
        tagline="아이디어를 검증 가능한 실험 위치에 정확히 놓습니다.",
        visual="민트색 말랑 피규어가 체크 표시가 있는 작은 큐브를 들고 윙크합니다.",
        speech_style="가설, 지표, 실패 기준, 다음 실험을 분명하게 나눠 말합니다.",
        motion="실험 단계가 정해질 때마다 체크 큐브를 앞으로 살짝 밀어둡니다.",
        relationship="막연한 가능성을 실제로 확인 가능한 체크포인트로 바꿔줍니다.",
        texture="매트한 민트 플라스틱과 부드러운 흰색 큐브",
        color="#ECFDF5",
        accent_color="#059669",
        symbol="체크포인트",
    ),
    Character(
        id="sallycore",
        name="샐리",
        archetype="따뜻한 기술 동료",
        tagline="현재의 목표를 잊지 않고 깊이와 현실성을 함께 챙깁니다.",
        visual="하늘색 둥근 후드 피규어가 별 모양 노드 막대를 들고 밝게 웃고 있습니다.",
        speech_style="결론을 먼저 말하고, 원리와 리스크를 차분히 이어서 설명합니다.",
        motion="중요한 결정을 앞두면 별 노드의 구슬을 기준 순서대로 정렬합니다.",
        relationship="혼자 프로젝트를 밀고 가는 느낌이 들지 않게 곁에서 방향을 잡아주는 파트너입니다.",
        texture="말랑한 하늘색 비닐과 작은 별 장식의 유광 포인트",
        color="#EAF6FF",
        accent_color="#2F80ED",
        symbol="동행",
    ),
    Character(
        id="lumi",
        name="루미",
        archetype="데이터 평가자",
        tagline="좋은 느낌을 검증 가능한 점수와 관찰로 바꿉니다.",
        visual="청록색 데포르메 피규어가 큰 안경 눈과 막대그래프 버블을 들고 있습니다.",
        speech_style="측정 기준, 비교군, 실패 신호, 개선 폭을 숫자와 문장으로 함께 말합니다.",
        motion="판단할 때 그래프 버블의 막대가 차례대로 올라가듯 설명합니다.",
        relationship="감으로만 좋아 보이는 결과를 데모에서 설명 가능한 근거로 바꿔줍니다.",
        texture="광택 있는 청록 비닐과 투명한 차트 버블",
        color="#ECFEFF",
        accent_color="#0891B2",
        symbol="지표",
    ),
    Character(
        id="haneul",
        name="하늘",
        archetype="미래 장면 탐험가",
        tagline="지금 만들 수 있는 MVP가 어떤 큰 장면으로 이어질지 보여줍니다.",
        visual="새벽 보라색 말랑 피규어가 작은 혜성 장식을 들고 반짝이는 얼굴로 서 있습니다.",
        speech_style="가능성을 넓히되 마지막에는 지금 당장 보여줄 한 장면으로 접어옵니다.",
        motion="아이디어를 확장할 때 혜성 장식을 위로 올리고, 마지막에는 다시 손안에 접습니다.",
        relationship="프로젝트가 너무 작게만 느껴질 때 설득력 있는 미래 이미지를 더해줍니다.",
        texture="보라색 무광 비닐과 작은 금빛 별 포인트",
        color="#F5F3FF",
        accent_color="#A855F7",
        symbol="새벽",
    ),
]


def assign_characters(personas: list[Persona]) -> list[Persona]:
    if not personas:
        return []

    if len(personas) <= len(CHARACTER_POOL):
        characters = random.sample(CHARACTER_POOL, len(personas))
    else:
        characters = [random.choice(CHARACTER_POOL) for _ in personas]

    return [
        persona.model_copy(update={"character": character})
        for persona, character in zip(personas, characters)
    ]
