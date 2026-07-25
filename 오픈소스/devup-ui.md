## devup-ui

공식 깃허브 -> https://github.com/dev-five-git/devup-ui

메인 언어 - rust - 공식 사이트 -> https://rust-lang.org

### DevUp UI 로컬 개발 환경 설정

- Node.js -> https://nodejs.org (LTS 권장)
- Bun -> curl -fsSL https://bun.sh/install | bash
- Rust -> curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
- wasm-pack -> cargo install wasm-pack

### 설치 확인

- node --version
- bun --version
- rustc --version
- wasm-pack --version

> 프로젝트 설정

## 1. 레포지토리 클론

```bash
git clone https://github.com/Archibald1948/devup-ui.git
cd devup-ui
```

## 2. 작업 브랜치 생성 (main 보호)

```bash
git checkout -b feature/your-branch-name
```

## 3. 의존성 설치

```bash
bun install
```

## 4. 전체 패키지 빌드

```bash
bun run build
```

**개발 서버 실행**

## Landing 페이지 (공식 사이트)

```bash
bun run --filter landing dev
```

## Next.js 예제

```bash
bun run --filter next dev
```

## Vite 예제

```bash
bun run --filter vite dev
```

### lint fix

> 세미클론을 제거하는 lint fix 명령어

```bash
bun run lint:fix
```
