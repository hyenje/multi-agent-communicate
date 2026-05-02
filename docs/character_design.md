# PersonaGraph Character Design

## 디자인 방향

PersonaGraph의 시각 방향은 현실적인 사람 초상이 아니라, 문제를 함께 토론하는 작고 말랑한 데포르메 피규어 팀이 더 잘 맞는다. 첫 화면은 캐릭터를 크게 세우지 않고, 에이전트 간 연결과 메시지 흐름이 느껴지는 추상 배너 배경을 사용한다. 페르소나 카드와 토론 네트워크에서는 각 에이전트를 굿즈처럼 구분되는 작은 캐릭터로 보여준다.

Google Drive의 개인 레퍼런스 문서와 연결된 Behance 레퍼런스를 함께 확인한 뒤 아래 기준으로 재해석했다. 레퍼런스는 그대로 복제하지 않고 분위기, 형태 언어, 부드러운 물성, 표현 강도만 가져온다.

- 말랑하고 굿즈 같은 물성
- 현실 사람보다 작은 피규어/인형에 가까운 데포르메
- 큰 눈, 작은 입, 둥근 볼륨처럼 표정을 즉시 읽을 수 있는 얼굴
- 따뜻한 크림색, 하늘색, 복숭아색, 민트, 연보라 중심의 절제된 색감
- 동화적이고 약간 애니메이션 같은 분위기
- 기술적 로봇감보다 살아 있는 작은 동료 같은 관계성
- 에이전트가 서로 연결되어 말하는 네트워크 모티프

## 레퍼런스 해석

- OOPS STRESS BALL: 둥근 실루엣, 굵은 눈매, 손에 잡히는 굿즈감, 밝은 배경의 장난감 같은 질감
- Character Reference 02 / Character Reference 04: 과장된 눈과 표정, 애니메이션식 얼굴 비율, 감정이 먼저 보이는 데포르메
- 3D Characters Mix: 단순한 몸체와 큰 얼굴, 3D 피규어의 매끈한 완성도, 일관된 조명
- Character Design 04 / HELPER Chapter II Manga: 선명한 표정, 강한 실루엣, 컷과 말풍선에서 오는 대화 에너지
- Mt s y tung 2 / Illustrations for a fairy tale: 동화적 색감, 장식적 포인트, 부드러운 배경 분위기

원문 링크: [OOPS STRESS BALL](https://www.behance.net/gallery/247783259/OOPS_STRESS-BALL), [Character Reference 02](https://www.behance.net/gallery/228822919/_), [Characters concept for Client](https://www.behance.net/gallery/235009745/Characters-concept-for-Client), [Character Reference 04](https://www.behance.net/gallery/199183793/_), [3D Characters Mix](https://www.behance.net/gallery/230809531/3D-Characters-Mix), [Character Design 04](https://www.behance.net/gallery/235160975/Character-Design-04), [Mt s y tung 2](https://www.behance.net/gallery/247002739/Mt-s-y-tung-2), [Illustrations for a fairy tale](https://www.behance.net/gallery/246428197/illustrations-for-a-fairy-tale), [HELPER Chapter II Manga](https://www.behance.net/gallery/247107577/HELPER-Chapter-II-Manga).

## 배너

현재 UI에는 `assets/hero/personagraph-agent-network.png`를 메인 배너 배경으로 사용한다. 사람이나 마스코트를 넣지 않고, 부드러운 책상 위에 노드, 얇은 연결선, 반투명 패널, 말풍선 형태가 떠 있는 장면으로 에이전트 간 의사소통을 표현한다.

배너 기준:

- 첫 화면에서 PersonaGraph의 분위기를 정한다.
- 왼쪽에는 제목과 설명이 올라갈 수 있도록 여백을 둔다.
- 메인 시각물은 캐릭터가 아니라 에이전트 네트워크다.
- 어두운 SF 느낌, 과한 보라색 그라디언트, 복잡한 기계 부품은 피한다.

## 페르소나 이미지 세트

페르소나는 데포르메 피규어형 캐릭터 10개를 사용한다. 각 이미지는 `assets/personas/` 아래 개별 PNG로 저장되어 있고, 실행 시 캐릭터 풀에서 임의 배정된다. 전체 시트는 `assets/personas/persona-deformed-sheet.png`로 보관한다.

- 노리: 작은 MVP 조율자
- 오르빗: 시스템 궤도 설계자
- 밀밀: 사용자 감정 번역가
- 소리: 발표 장면 연출가
- 모리: 조용한 리스크 관찰자
- 결: 결론 직조가
- 자리: 실험 자리잡이
- 샐리: 따뜻한 기술 동료
- 루미: 데이터 평가자
- 하늘: 미래 장면 탐험가

이미지 생성 기준:

- 모두 오리지널 캐릭터여야 하며 특정 작품이나 작가의 그림을 복제하지 않는다.
- 현실 사람 초상, 실사 사진, 성인 비율 인체처럼 보이지 않게 한다.
- 큰 눈과 작은 입, 둥근 몸, 짧은 팔다리, 액세서리 하나로 역할을 즉시 읽게 한다.
- 각 캐릭터 뒤에 작은 노드/연결선 모티프를 넣어 AI 에이전트임을 암시한다.
- UI 카드 안에서 식별 가능하도록 표정, 색, 역할 액세서리가 서로 달라야 한다.
- 설명 가능한 MVP 자산이어야 하므로 각 이미지와 역할 이름이 명확히 연결되어야 한다.

## UI 적용

첫 화면은 배너 이미지 위에 제목과 설명을 올리는 히어로 영역이다. 캐릭터 이미지는 메인 첫 화면에 크게 노출하지 않는다.

토론 실행 결과에는 `토론 네트워크` 영역을 추가해 각 데포르메 페르소나가 연결선으로 이어지게 표시한다. 왼쪽 페르소나 카드에는 각 캐릭터 이미지와 역할 설명을 함께 보여주어, 단순 로그가 아니라 여러 작은 에이전트가 한 문제를 두고 대화하는 느낌을 만든다.
