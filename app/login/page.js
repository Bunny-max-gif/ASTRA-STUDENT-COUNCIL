'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '../../lib/supabase';

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [err, setErr] = useState('');
  const [info, setInfo] = useState('');

  async function login(e) {
    e.preventDefault();
    setErr(''); setInfo('');
    const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password: pw });
    if (error) return setErr('Email or password is incorrect.');
    router.push('/staff');
  }

  async function forgot() {
    setErr(''); setInfo('');
    if (!email.trim()) return setErr('Type your email first.');
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), { redirectTo: location.origin + '/set-password' });
    if (error) setErr(error.message);
    else setInfo('If that email has an account, a reset link is on its way.');
  }

  return (
    <>
      <h2>Staff login</h2>
      <div className="note">For coordinators and council officers. Students do not need to log in to view the dashboard.</div>
      <form onSubmit={login}>
        <label>College email<input type="email" required autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" required autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} /></label>
        {err && <div className="err" role="alert">{err}</div>}
        {info && <div className="meta">{info}</div>}
        <div className="acts"><button className="pri" type="submit">Log in</button><button type="button" onClick={forgot}>Forgot password</button></div>
      </form>
    </>
  );
}
