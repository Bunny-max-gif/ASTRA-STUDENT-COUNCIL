import './globals.css';
import Header from '../components/Header';

export const metadata = {
  title: 'ASTRA Student Council | Student life, engineered together',
  description: 'Discover ASTRA student clubs, events, projects, and council updates. Find your people and make something matter.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
      </body>
    </html>
  );
}
