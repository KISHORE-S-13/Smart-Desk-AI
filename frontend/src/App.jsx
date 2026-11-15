import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import AdminOverview from "./components/AdminOverview";
import TicketList from "./components/TicketList";
import KnowledgeView from "./components/KnowledgeView";
import CreateTicketModal from "./components/CreateTicketModal";
import TicketDetailModal from "./components/TicketDetailModal";
import ChatbotDrawer from "./components/ChatbotDrawer";
import LoginPage from "./components/LoginPage";

function MainDashboard() {
  const { user, isAdmin, loading } = useAuth();
  const [activeTab, setActiveTab] = useState(isAdmin ? "overview" : "my-tickets");
  const [ticketSection, setTicketSection] = useState("in_progress");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  if (loading) {
    return (
      <div className="app-loading-screen">
        <div className="loading-spinner"></div>
        <p>Initializing SmartDesk AI...</p>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const handleOpenSubmitTicket = () => {
    setActiveTab(isAdmin ? "tickets" : "my-tickets");
    setTicketSection("submit");
  };

  const handleOpenTickets = () => {
    setActiveTab(isAdmin ? "tickets" : "my-tickets");
    setTicketSection("in_progress");
  };

  const handleTicketCreated = (newTicket) => {
    setSelectedTicket(newTicket);
    setTicketSection("in_progress");
    setRefreshKey((k) => k + 1);
  };

  const handleTicketUpdated = (updatedTicket) => {
    setSelectedTicket(updatedTicket);
    setRefreshKey((k) => k + 1);
  };

  const handleTicketDeleted = () => {
    setSelectedTicket(null);
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="smartdesk-app-layout">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenCreateTicket={handleOpenSubmitTicket}
        onOpenTickets={handleOpenTickets}
        onOpenChatbot={() => setIsChatbotOpen(true)}
      />

      <div className="app-main-viewport">
        <Navbar onOpenChatbot={() => setIsChatbotOpen(true)} />

        <main className="app-content-container">
          {isAdmin ? (
            <>
              {activeTab === "overview" && (
                <AdminOverview
                  key={refreshKey}
                  onSelectTicket={(t) => setSelectedTicket(t)}
                  onNavigateSection={(sec) => {
                    setActiveTab("tickets");
                    setTicketSection(sec);
                  }}
                />
              )}
              {activeTab === "tickets" && (
                <TicketList
                  key={`${refreshKey}-${ticketSection}`}
                  initialSection={ticketSection}
                  onSelectTicket={(t) => setSelectedTicket(t)}
                  onOpenCreateTicket={handleOpenSubmitTicket}
                />
              )}
              {activeTab === "knowledge" && (
                <KnowledgeView onOpenChatbot={() => setIsChatbotOpen(true)} />
              )}
            </>
          ) : (
            <>
              {activeTab === "my-tickets" && (
                <TicketList
                  key={`${refreshKey}-${ticketSection}`}
                  initialSection={ticketSection}
                  onSelectTicket={(t) => setSelectedTicket(t)}
                  onOpenCreateTicket={handleOpenSubmitTicket}
                />
              )}
              {activeTab === "knowledge" && (
                <KnowledgeView onOpenChatbot={() => setIsChatbotOpen(true)} />
              )}
            </>
          )}
        </main>
      </div>

      {/* Modals & Drawers */}
      {isCreateModalOpen && (
        <CreateTicketModal
          onClose={() => setIsCreateModalOpen(false)}
          onTicketCreated={handleTicketCreated}
        />
      )}

      {selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onTicketUpdated={handleTicketUpdated}
          onTicketDeleted={handleTicketDeleted}
        />
      )}

      <ChatbotDrawer
        isOpen={isChatbotOpen}
        onClose={() => setIsChatbotOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainDashboard />
    </AuthProvider>
  );
}