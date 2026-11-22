import {
  AudioLines,
  History,
  Image,
  LayoutDashboard,
  Link2,
  ScanSearch,
  Settings,
  Sparkles,
} from "lucide-react";

export const NAV_ITEMS = [
  { to: "/", key: "overview", icon: LayoutDashboard, end: true },
  { to: "/scanner", key: "scanner", icon: ScanSearch, end: false },
  { to: "/screenshot", key: "screenshot", icon: Image, end: false },
  { to: "/url", key: "url", icon: Link2, end: false },
  { to: "/voice", key: "voice", icon: AudioLines, end: false },
  { to: "/history", key: "history", icon: History, end: false },
  { to: "/insights", key: "insights", icon: Sparkles, end: false },
  { to: "/settings", key: "settings", icon: Settings, end: false },
] as const;
