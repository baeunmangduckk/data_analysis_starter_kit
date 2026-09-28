import { NavMain } from "@/components/layout/nav-main";
import { Sidebar, SidebarContent, SidebarHeader } from "@/components/ui/sidebar";

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex flex-col gap-0.5 px-2 py-1 group-data-[collapsible=icon]:hidden">
          <span className="text-sm font-semibold">K-Pop 산업 대시보드</span>
          <span className="text-xs text-muted-foreground">전망 및 지표 분석</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMain />
      </SidebarContent>
    </Sidebar>
  );
}
