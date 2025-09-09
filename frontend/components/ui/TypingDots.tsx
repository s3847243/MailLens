import React from "react";

export default function TypingDots() {
  return (
    <div className="flex items-center gap-1 h-5">
      <span className="dot" />
      <span className="dot" />
      <span className="dot" />
      <style>{`
        .dot {
          width: 6px;
          height: 6px;
          border-radius: 9999px;
          background: currentColor;
          display: inline-block;
          animation: dot-bounce 1.2s infinite ease-in-out;
          transform-origin: center;
        }
        .dot:nth-child(1) { animation-delay: 0s;   }
        .dot:nth-child(2) { animation-delay: 0.15s; }
        .dot:nth-child(3) { animation-delay: 0.30s; }

        @keyframes dot-bounce {
          0%, 60%, 100% { transform: scale(0.6); opacity: 0.6; }
          30%           { transform: scale(1);   opacity: 1;   }
        }
      `}</style>
    </div>
  );
}
