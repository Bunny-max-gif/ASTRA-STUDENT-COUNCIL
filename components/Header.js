'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase, arrivedViaLink } from '../lib/supabase';

export default function Header() {
  const [user, setUser] = useState(null);
  const router = useRouter();

  useEffect(() => {
    if (arrivedViaLink) router.replace('/set-password');
    supabase.auth.getSession().then(({ data }) => setUser(data.session?.user ?? null));
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
      if (event === 'PASSWORD_RECOVERY') router.replace('/set-password');
    });
    return () => sub.subscription.unsubscribe();
  }, [router]);

  async function logout() {
    await supabase.auth.signOut();
    router.push('/');
  }

  return (
    <header>
      <div className="top">
        <Link href="/" className="brand">
          <img src="/logo.png" alt="ASTRA logo" />
          <span>ASTRA <span className="brand-sub">STUDENT COUNCIL</span></span>
        </Link>
        <nav>
          <Link href="/#whats-happening">What&apos;s on</Link>
          <Link href="/#community">Our community</Link>
          <Link href="/#budget">Transparency</Link>
          {user ? (
            <>
              <Link href="/staff" className="nav-login">Staff area</Link>
              <button className="nav-login" onClick={logout}>Log out</button>
            </>
          ) : (
            <Link href="/login" className="nav-login">Staff login</Link>
          )}
        </nav>
      </div>
    </header>
  );
}
