# RSS-MOTD Codex 인수인계

마지막 정리일: 2026-07-17 (KST)

이 문서는 다른 컴퓨터의 새로운 Codex 채팅에서 작업을 이어가기 위한 인수인계 자료다. 먼저 이 문서와 `README.md`를 모두 읽고, 실제 저장소 상태를 확인한 뒤 작업한다.

## 새 Codex에 전달할 첫 요청 예시

```text
이 저장소의 후속 작업을 이어서 진행하려고 해.
먼저 CODEX_HANDOFF.md와 README.md를 끝까지 읽고 git status, 현재 브랜치,
원격 브랜치와 최근 커밋을 확인해줘. 기존 기능과 사용자 결정을 유지하고,
변경하기 전에 현재 구현을 기준으로 판단해줘.
```

## 저장소와 현재 상태

- GitHub 저장소: `https://github.com/sj58320/test`
- 공개 사이트: `https://sj58320.github.io/test/`
- 기준 브랜치: `main`
- 이 문서 작성 시 `main` HEAD: `06f4cf057db252626dc861d99df84b8f366a77a8`
- 마지막 병합 PR: `#8 feat: add manageable skin preview catalog`
- PR 주소: `https://github.com/sj58320/test/pull/8`
- `feat/skin-preview-cms` 브랜치는 PR #8 병합 후 로컬과 원격에서 삭제했다.
- 원격에는 `main`, `dev`가 남아 있다. `dev`는 `main`보다 오래된 상태이므로 새 작업은 최신 `main`에서 `feat/...` 브랜치를 만드는 편이 안전하다.
- 현재 PC에만 `feat/pages-cms`라는 오래된 로컬 브랜치가 남아 있으나 원격 브랜치가 아니며 사용하지 않는다.
- 저장소 루트에는 프로젝트용 `AGENTS.md`가 없다. 기존 외부 ChatGPT Pro 검토 지침은 이전 PC의 전역 Codex 설정에만 있었다.

## 새 컴퓨터에서 시작하기

```powershell
git clone https://github.com/sj58320/test.git
cd test
git switch main
git pull --ff-only origin main
node scripts/validate-content.mjs
node --test scripts/discord-news-converter.test.mjs
python -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 연다. JSON을 `fetch`하므로 `index.html`을 파일로 직접 열지 않는다. VS Code Live Server를 사용해도 된다.

## 서비스 성격과 기술 제약

- CS2 RSS 좀비탈출 서버의 규칙·FAQ·명령어·용어·공지·스킨을 잠깐 확인하는 정적 위키형 사이트다.
- 별도 서버 없이 GitHub Pages로 서비스한다.
- HTML, CSS, JavaScript와 JSON으로 구성된 정적 사이트다.
- PicoCSS 의존성은 제거했고 현재 스타일은 자체 CSS로 유지한다.
- PWA, 홈 화면 설치, 오프라인 캐시, favicon, URL 공유용 OG 이미지는 사용자 요청으로 제거했다.
- Steam 로그인이나 사용자별 비공개 페이지는 구현하지 않았다. 정적 GitHub Pages만으로 Steam OpenID 비밀 처리와 안전한 세션 관리는 어렵고 외부 백엔드 또는 서버리스 함수가 필요하다.

## 현재 화면 구성

상단 탭은 다음 다섯 개다.

1. FAQ
2. 명령어 목록
3. 용어 사전
4. 공지
5. 스킨 프리뷰

공통 UI:

- 한국어, English, 日本語 언어 버튼
- URL의 `?lang=ko|en|jp`로 선택 언어 유지
- 좌우 방향키로 탭 이동
- 탭 클릭은 특정 콘텐츠 위치로 강제 스크롤하지 않고 화면만 전환
- 화면을 내리면 하단 중앙에 맨 위로 이동 버튼 표시
- 복사 완료 토스트 알림은 현재 언어로 표시
- 상단 소셜 링크는 Discord와 Steam 그룹을 아이콘으로 표시하며 GitHub 링크는 제거
- Steam 그룹: `https://steamcommunity.com/groups/Revenant_Server`

## 구현된 주요 기능

### 통합 검색

- FAQ, 명령어, 용어, 공지를 검색한다.
- 스킨 프리뷰는 통합 검색 대상에서 제외하고 스킨 탭에서는 상단 통합 검색창도 숨긴다.
- 한국어 초성 검색을 지원한다. 예: `ㄱㅈ`로 `고좀` 검색.
- 명령어 검색은 `!stopsound`, `/stopsound`, `stopsound`를 같은 명령어로 정규화한다.
- 명령어 결과는 정확 일치, 접두사, 별칭, 설명 순으로 우선한다.
- 명령어 카테고리와 섹션 이름도 검색 대상이다.
- 공지 검색 결과는 일치한 줄을 중심으로 표시한다.
- 검색 결과는 FAQ·명령어·용어·공지별로 시각적으로 구분한다.

### FAQ

- `data/faq.json`의 블록 구조로 렌더링한다.
- `처음이라면 여기부터` 빠른 시작 영역이 있다.
- FAQ 관련 항목 연결을 지원한다.
- FAQ 안의 명령어 표기는 `/` 접두사로 통일했다.
- 답변 블록: `text`, `inlineCode`, `code`, `link`, `image`, `break`, `spacer`.
- 번역 문구는 주로 `assets/js/lang.js`의 `langKey`로 관리한다.

### 명령어 목록

- 데이터: `data/commands.json`.
- 카테고리 필터, 검색, 즐겨찾기를 지원한다.
- 즐겨찾기는 브라우저 `localStorage`에만 저장되며 기기 간 동기화되지 않는다.
- 복사 시 `!` 명령도 `/`로 복사하고, `<0~100>` 같은 인자 설명은 제외한 명령어 본체와 뒤 공백 한 칸을 복사한다.
- 명령어 설명도 검색 대상이다.

### 용어 사전

- 데이터: `data/terms.json`.
- `locales.ko`, `locales.jp`가 있으며 영어 용어집은 준비 중이다.
- 한국어·영어·일본어 용어집 내용이 서로 다를 수 있으므로 자동 번역하거나 억지로 맞추지 않는다.
- 기본 목록에서는 용어를 일정한 높이로 보여주고, 마우스 hover나 키보드 focus 시 설명·별칭을 팝오버로 표시한다.
- 링크 복사 버튼은 작은 아이콘 형태다.

### Discord 공지

- 데이터: `data/news.json`.
- `scripts/sync-discord-news.mjs`가 Discord REST API에서 공지를 가져온다.
- `scripts/discord-news-converter.mjs`가 웹 표시용으로 변환한다.
- 제목은 앞쪽 멘션 줄을 건너뛴 뒤 첫 번째 의미 있는 줄에서 만든다.
- Discord Markdown의 제목, 굵게, 목록, 인용문, 링크, 인라인 코드와 코드 블록을 `markdown-it`으로 렌더링한다.
- 사용자·역할 멘션은 숫자 ID 대신 `@서버닉네임`, `@역할명`으로 표시한다. 이름을 찾을 수 없으면 숫자 ID를 노출하지 않는다.
- 작성자는 Discord 계정 기본 이름이 아니라 서버 닉네임을 우선한다.
- PatchNote와 Notice 두 채널을 함께 읽고 카드에 출처 채널명을 표시한다.
- 공지 카드는 hover 시 배경과 굵은 테두리로 구역을 강조한다.
- 공지 영역 너비를 사용자가 가로로 드래그해 조절할 수 있다.
- 긴 한 줄은 잘리지 않고 영역 너비에 맞춰 줄바꿈된다.
- `updatedAt`은 가장 최근 메시지의 작성 또는 수정 시각으로 자동 계산한다.
- 원문 URL이 실제 Discord 메시지 주소일 때만 의미가 있다. 단순 초대 링크를 원문 링크로 사용하지 않는다.

Discord 공식 서버 설정:

- Guild ID: `850664390779731978`
- PatchNote 채널 ID: `853637982552326144`
- Notice 채널 ID: `1168514920539758683`

GitHub Actions 설정 이름:

- Secret: `DISCORD_BOT_TOKEN` — 값은 절대 문서나 코드에 적지 않는다.
- Variable: `DISCORD_GUILD_ID`
- Variable: `DISCORD_NEWS_CHANNEL_IDS`
- Variable: `DISCORD_NEWS_LIMIT`
- Variable: `DISCORD_NEWS_ENABLED`

공지 동기화는 매시 `7, 22, 37, 52분`에 실행된다. Discord 내용이 바뀌지 않으면 커밋하지 않는다. 수정 또는 삭제된 공지도 다음 동기화 때 현재 채널 상태에 맞게 `data/news.json`에 반영된다.

### 스킨 프리뷰

- 데이터: `data/skins.json`.
- 미디어: `assets/skins/`.
- 인간, 좀비, 무기로 나뉜다.
- 무기는 주무기, 보조무기, 근접무기, 투척무기로 나뉜다.
- 주무기는 기관단총, 소총, 산탄총, 기관총, 저격총, 기타로 나뉜다.
- 주무기 `전체` 보기에서도 무기군별 섹션으로 묶어 표시한다.
- 선택된 필터는 밝게, 선택되지 않은 필터는 어둡게 표시하고 hover 시 살짝 밝아진다.
- 카드에 불필요한 `인간`, `좀비`, `무기` 반복 제목을 표시하지 않는다.
- 한국어 UI에서는 `nameKo`가 있으면 한국어 이름, 없으면 `name`을 사용한다. 영어와 일본어 UI에서는 영문 `name`을 사용한다.
- 이미지와 영상은 새 창 대신 페이지 내 모달로 열고 X, 바깥 클릭, Escape로 닫는다.
- 영상만 있는 항목도 첫 프레임을 썸네일처럼 표시한다.
- 한 스킨에 이미지와 영상이 여러 개 있어도 `media` 배열 안에서 함께 표시한다.

현재 규모:

- 스킨 223개: 인간 90, 좀비 6, 무기 127
- 미디어 항목 319개
- `assets/skins/` 파일 약 320개, 약 155.4 MiB

## Pages CMS

- 외부 오픈소스 서비스: `https://app.pagescms.org`
- UI 자체는 이 프로젝트가 만든 것이 아니다.
- 저장소 루트의 `.pages.yml`이 편집 필드, 미디어 위치와 커밋 메시지를 정의한다.
- 사이트의 `관리하기` 버튼은 `https://app.pagescms.org/sj58320/test/main`을 연다.
- Pages CMS GitHub App은 `sj58320/test`에 설치되어 있다.
- 편집 권한은 GitHub 저장소 권한과 Pages CMS GitHub App 접근 권한에 따른다.
- 저장 버튼을 누르면 현재 `main`에 Git 커밋이 생기고 검증 및 Pages 배포가 실행된다.
- 현재 커밋 메시지 템플릿: `content(skins): update {path}`.

중요한 성능 문제:

- 현재 Pages CMS가 `data/skins.json` 한 파일 안의 스킨 223개와 미디어 319개를 하나의 거대한 중첩 폼으로 렌더링한다.
- 이 때문에 Pages CMS 관리 화면이 매우 느리다. 작은 데이터에서 정상적으로 기대하는 속도보다 확실히 느리지만 현재 구조에서는 발생할 만한 현상이다.
- 장기적으로는 `스킨 하나 = JSON 파일 하나`인 Pages CMS collection 구조로 바꾸고, GitHub Action 또는 생성 스크립트가 이를 기존 `data/skins.json`으로 합치는 방식이 권장된다. 아직 구현하지 않았다.

Pages CMS 첫 저장 시 확인된 정규화:

- 기존 인간·좀비의 `subcategory: null` 96개가 제거됐다.
- 주무기가 아닌 항목의 `weaponType: null` 58개가 제거됐다.
- 비어 있던 무기 `nameKo` 127개가 제거됐다.
- 현재 원격 `main`에는 `subcategory: null`이 없고, 무기 127개에만 실제 `subcategory`가 남아 있다.
- 주무기 69개에만 실제 `weaponType`이 남아 있다.
- 웹 코드는 없는 키와 `null`을 동일하게 안전하게 처리한다. 인간·좀비의 `subcategory`, 주무기가 아닌 항목의 `weaponType`, 빈 `nameKo`는 없어도 표시상 문제없다.
- 단, `scripts/build_skin_previews.py`를 다시 실행하면 인간·좀비에 `subcategory: null`, 비어 있는 `nameKo` 등이 다시 만들어질 수 있다. 생성 스크립트와 CMS 정규화 형식을 맞추는 후속 정리가 필요할 수 있다.

## 스킨 원본 생성 폴더

다음 로컬 추출 폴더는 용량 때문에 Git에 올리지 않고 `.gitignore`에 등록돼 있다.

- `Human_Skin_List_Extract/`
- `Zombie_Skin_List_Extract/`
- `Primary_Weapon_Skin_List_Extract/`
- `Secondary_Weapon_Skin_List_Extract/`
- `Knife_Skin_List_Extract/`
- `Throwing_Weapon_Skin_List_Extract/`

재생성 명령:

```powershell
python scripts/build_skin_previews.py
```

Pillow가 필요하다. 실행 후 반드시 `node scripts/validate-content.mjs`를 실행하고 `data/skins.json`의 예상하지 않은 대규모 정규화 diff를 검토한다.

Discord 스킨 쓰레드에서 새 스킨을 자동 수집하는 기능은 논의만 했고 구현하지 않았다. 현재 추출 폴더와 생성 스크립트 또는 Pages CMS를 사용한다.

## 파일 구조

```text
/
├─ index.html
├─ .pages.yml
├─ data/
│  ├─ faq.json
│  ├─ commands.json
│  ├─ terms.json
│  ├─ news.json
│  └─ skins.json
├─ assets/
│  ├─ css/style.css
│  ├─ js/script.js
│  ├─ js/lang.js
│  ├─ images/guide/
│  └─ skins/
├─ scripts/
│  ├─ build_skin_previews.py
│  ├─ discord-news-converter.mjs
│  ├─ discord-news-converter.test.mjs
│  ├─ sync-discord-news.mjs
│  └─ validate-content.mjs
├─ vendor/
│  ├─ es-hangul.mjs
│  └─ markdown-it.min.js
└─ .github/workflows/
   ├─ validate-content.yml
   ├─ deploy-pages.yml
   └─ sync-discord-news.yml
```

## GitHub Actions와 Pages

### `validate-content.yml`

- 모든 PR에서 실행한다.
- `main`, `dev` 푸시에서도 실행한다.
- JSON·참조 미디어·번역 키 등을 검증한다.
- Discord 공지 변환 테스트를 실행한다.

### `deploy-pages.yml`

- `main` 푸시에서 실행한다.
- 콘텐츠를 검증한 뒤 GitHub Pages에 배포한다.
- `workflow_dispatch`, `workflow_call`도 지원한다.

### `sync-discord-news.yml`

- 15분 간격으로 Discord 공지를 확인한다.
- 변경이 있을 때만 `data/news.json`을 `main`에 커밋한다.
- 변경 커밋 후 `deploy-pages.yml`을 호출한다.

GitHub Pages 저장소 설정은 `Deploy from a branch`가 아니라 **GitHub Actions**다. 실제 배포 워크플로는 `main`만 체크아웃하므로 배포 기준 브랜치는 `main`이다. PR #8 병합 커밋 `06f4cf0`의 Pages 배포 성공을 확인했다.

## 작업 규칙과 사용자 선호

- 사용자와는 한국어로 대화한다.
- 새 기능 브랜치 이름은 `feat/...` 형태를 선호한다. 브랜치 이름에 `codex`를 넣지 않는다.
- 큰 변경은 기능 브랜치에서 작업하고 PR로 `main`에 병합한다.
- 사용자 변경이나 관련 없는 dirty worktree를 덮어쓰지 않는다.
- 사용자가 명시하지 않은 PWA, 로그인, favicon, 공유 미리보기 같은 기능을 임의로 추가하지 않는다.
- 이미지 예시를 새로 만드는 것보다 실제 HTML/CSS로 빠르게 시제품을 보여주는 편을 선호한다.
- 외부 ChatGPT Pro 검토가 크게 도움 된다고 판단하면 먼저 사용자에게 허락을 받아야 한다. 허락 후에는 ChatGPT의 `Pro` 모델과 `SJ` 프로젝트에서 새 채팅으로 질문한다. 오래 걸릴 수 있으므로 허락 없이 보내지 않는다.
- 이전 PC에서 `gh auth status`는 로컬 GitHub CLI 토큰 만료를 표시했다. Git 작업과 연결된 GitHub 앱은 동작했지만, 새 PC에서 CLI를 쓸 때는 `gh auth login` 후 `gh auth status`를 확인한다.

## 커밋 전 최소 검증

```powershell
git diff --check
node scripts/validate-content.mjs
node --test scripts/discord-news-converter.test.mjs
```

UI를 변경했다면 Live Server 또는 `python -m http.server 8000`으로 열고 다음을 확인한다.

- 데스크톱과 모바일 반응형 화면
- 5개 탭 전환과 URL 상태
- 언어 변경
- 통합 검색 결과 분류
- 키보드 좌우 탭 이동
- 복사 토스트
- 공지 Markdown과 긴 줄 줄바꿈
- 스킨 필터, 영상 썸네일과 모달

## 마지막으로 완료한 작업

1. `feat/skin-preview-cms`에서 Pages CMS 스킨 관리 기능을 구현했다.
2. Pages CMS에서 사용자 이름 수정 테스트를 수행해 `data/skins.json` 커밋이 생성되는 것을 확인했다.
3. Pages CMS의 첫 저장이 불필요한 `null`과 빈 선택 필드를 제거하는 것을 확인했다.
4. 관리 버튼을 Pages CMS `main` 브랜치로 변경했다.
5. PR #8의 검증이 통과한 뒤 `main`에 병합했다.
6. GitHub Pages 소스를 GitHub Actions로 되돌리고 `main` 배포 성공을 확인했다.
7. `feat/skin-preview-cms` 브랜치를 로컬과 원격에서 삭제했다.
8. 로컬 작업 디렉터리는 최신 `main`으로 전환했다.

## 아직 하지 않은 개선 후보

- Pages CMS 성능 개선을 위한 스킨별 JSON collection 전환
- `build_skin_previews.py` 출력 형식을 Pages CMS가 저장하는 선택 필드 생략 방식과 일치시키기
- Discord 스킨 쓰레드에서 새 스킨을 자동 수집하는 별도 동기화 파이프라인
- 영어 용어집 작성
- Pages CMS 사용 중 실제 편집 흐름을 더 테스트하고 필드 순서·설명을 다듬기

위 후보는 자동으로 착수하지 말고 사용자와 범위·구조를 먼저 합의한다.
