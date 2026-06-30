import './globals.css';

export const metadata = {
  title: 'NGO Donation Management',
  description: 'Donation management system for NGOs',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
