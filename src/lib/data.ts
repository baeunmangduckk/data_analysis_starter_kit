import fs from "node:fs/promises";
import path from "node:path";
import { connection } from "next/server";
import type { PageData, SourcesData } from "@/types/page";

const DATA_DIR = path.join(process.cwd(), "public", "data");

// 파일이 없으면(아직 npm run etl을 안 돌린 경우) null을 돌려 페이지가 안내 화면을 보여주게 한다.
// JSON 문법 오류 같은 그 밖의 실패는 그대로 던져 error.tsx가 처리한다.
export async function readData<T>(filename: string): Promise<T | null> {
  // 프로덕션 빌드가 JSON을 정적으로 굳히지 않도록 요청 시점까지 렌더링을 미룬다.
  // 반드시 페이지 컴포넌트 함수 "안"에서 호출해야 etl 재실행 결과가 바로 반영된다.
  // 단, GitHub Pages 정적 export 빌드(NEXT_OUTPUT_EXPORT=true)는 서버가 없어
  // "요청 시점"이 존재하지 않으므로 이 경우에만 건너뛰고 빌드 시점 값을 그대로 굳힌다.
  if (process.env.NEXT_OUTPUT_EXPORT !== "true") {
    await connection();
  }
  try {
    const raw = await fs.readFile(path.join(DATA_DIR, filename), "utf-8");
    return JSON.parse(raw) as T;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw error;
  }
}

export function getPage(slug: string): Promise<PageData | null> {
  return readData<PageData>(`${slug}.json`);
}

export function getSources(): Promise<SourcesData | null> {
  return readData<SourcesData>("sources.json");
}
