import {
  Bot,
  BookOpen,
  ChartColumn,
  Globe,
  House,
  Landmark,
  MessageCircle,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  // public/data/<slug>.json 파일명과 라우트 폴더명을 겸하는 식별자
  slug: string;
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

// 사이드바와 홈의 주제 링크 카드가 함께 쓰는 단일 출처.
// 페이지를 추가할 때는 여기 한 곳에 항목을 넣고 라우트 폴더를 만든다.
export const NAV_ITEMS: NavItem[] = [
  {
    slug: "home",
    href: "/",
    label: "홈",
    description: "핵심 지표와 인사이트 요약",
    icon: House,
  },
  {
    slug: "market",
    href: "/market",
    label: "시장 전망",
    description: "글로벌 음반 매출, 앨범 수출 추이, 콘서트 시장 전망",
    icon: TrendingUp,
  },
  {
    slug: "concentration",
    href: "/concentration",
    label: "판매 집중도·양극화",
    description: "Top100 판매 집중도, Gini 추이, 제작비·공연 격차, 그룹 생존율",
    icon: ChartColumn,
  },
  {
    slug: "finance",
    href: "/finance",
    label: "기획사 재무",
    description: "하이브·SM·YG·JYP 매출과 영업이익 비교",
    icon: Landmark,
  },
  {
    slug: "fans",
    href: "/fans",
    label: "팬 반응",
    description: "YouTube 댓글 감성과 아티스트 팬덤 지표",
    icon: MessageCircle,
  },
  {
    slug: "global",
    href: "/global",
    label: "글로벌 확장",
    description: "지역별 수출 재편과 신흥시장 성장",
    icon: Globe,
  },
  {
    slug: "ai-virtual",
    href: "/ai-virtual",
    label: "AI·버추얼 아이돌",
    description: "버추얼 아이돌 시장 규모 전망과 사례",
    icon: Bot,
  },
  {
    slug: "sources",
    href: "/sources",
    label: "출처",
    description: "모든 지표의 출처와 사용처",
    icon: BookOpen,
  },
];

export function getNavItem(slug: string): NavItem {
  const item = NAV_ITEMS.find((navItem) => navItem.slug === slug);
  if (!item) {
    throw new Error(`nav.ts에 등록되지 않은 slug입니다: ${slug}`);
  }
  return item;
}
