import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ChatPage } from "./pages/ChatPage";
import { RagExplorerPage } from "./pages/RagExplorerPage";
import { StatusPage } from "./pages/StatusPage";

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppShell>
            <ChatPage />
          </AppShell>
        }
      />
      <Route
        path="/explorer"
        element={
          <AppShell>
            <RagExplorerPage />
          </AppShell>
        }
      />
      <Route
        path="/status"
        element={
          <AppShell>
            <StatusPage />
          </AppShell>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
