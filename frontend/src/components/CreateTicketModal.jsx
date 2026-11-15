import React from "react";
import { X } from "lucide-react";
import TicketSubmissionForm from "./TicketSubmissionForm";

export default function CreateTicketModal({ onClose, onTicketCreated }) {
  const handleTicketCreated = (newTicket) => {
    if (onTicketCreated) {
      onTicketCreated(newTicket);
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container create-ticket-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-left">
            <h3 className="modal-title">Create IT Incident or Service Request</h3>
          </div>
          <button className="btn-close-modal" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <TicketSubmissionForm
          onTicketCreated={handleTicketCreated}
          onCancel={onClose}
          isEmbedded={false}
        />
      </div>
    </div>
  );
}