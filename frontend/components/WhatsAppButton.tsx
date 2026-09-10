import React from 'react';

interface WhatsAppButtonProps {
  phone?: string;
  message?: string;
  label?: string;
  className?: string;
}

const DEFAULT_PHONE = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '27744545665';
const DEFAULT_MESSAGE = "Hi Alpha LPGas, I'd like to place an order.";

export default function WhatsAppButton({
  phone = DEFAULT_PHONE,
  message = DEFAULT_MESSAGE,
  label = 'Order on WhatsApp',
  className = '',
}: WhatsAppButtonProps) {
  const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;

  return (
    <a
      target="_blank"
      rel="noopener noreferrer"
      href={url}
      className={`inline-flex items-center justify-center gap-2 bg-[#25D366] hover:bg-[#22c35e] text-white font-semibold rounded-full px-6 md:px-5 py-3 md:py-2.5 text-sm transition-colors cursor-pointer w-full md:w-auto min-h-[44px] ${className}`}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-4 h-4"
        aria-hidden="true"
      >
        <path d="M2.992 16.342a2 2 0 0 1 .094 1.167l-1.065 3.29a1 1 0 0 0 1.236 1.168l3.413-.998a2 2 0 0 1 1.099.092 10 10 0 1 0-4.777-4.719" />
      </svg>
      {label}
    </a>
  );
}
