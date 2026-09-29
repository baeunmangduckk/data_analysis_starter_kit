import type { NextConfig } from "next";

// GitHub Actions 워크플로우(.github/workflows/deploy-pages.yml)가 빌드 시에만 설정하는 플래그.
// 로컬 npm run dev/build/start는 이 값이 없어 기존 동작(요청 시점 렌더링)을 그대로 유지한다.
const isStaticExport = process.env.NEXT_OUTPUT_EXPORT === "true";

const nextConfig: NextConfig = {
  ...(isStaticExport
    ? {
        output: "export",
        // GitHub Pages 프로젝트 페이지(https://<user>.github.io/<repo>/) 하위 경로 대응.
        basePath: "/data_analysis_starter_kit",
      }
    : {}),
};

export default nextConfig;
