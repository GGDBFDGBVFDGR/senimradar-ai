import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell.tsx";
import { LanguageProvider } from "./i18n/LanguageProvider.tsx";
import { HistoryPage } from "./pages/HistoryPage.tsx";
import { InsightsPage } from "./pages/InsightsPage.tsx";
import { NotFoundPage } from "./pages/NotFoundPage.tsx";
import { OverviewPage } from "./pages/OverviewPage.tsx";
import { ScannerPage } from "./pages/ScannerPage.tsx";
import { ScreenshotPage } from "./pages/ScreenshotPage.tsx";
import { SettingsPage } from "./pages/SettingsPage.tsx";
import { UrlPage } from "./pages/UrlPage.tsx";
import { VoicePage } from "./pages/VoicePage.tsx";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "scanner", element: <ScannerPage /> },
      { path: "screenshot", element: <ScreenshotPage /> },
      { path: "url", element: <UrlPage /> },
      { path: "voice", element: <VoicePage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "insights", element: <InsightsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

export default function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: false,
            refetchOnWindowFocus: false,
            staleTime: 15_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <RouterProvider router={router} />
      </LanguageProvider>
    </QueryClientProvider>
  );
}
