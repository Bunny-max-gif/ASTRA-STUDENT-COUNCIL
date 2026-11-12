'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '../../lib/supabase';

export default function SetPassword() {
  const router = useRouter();
  const [pw, setPw] = useState('');
  const [err, setErr] = useState('');

  async function save(e) {
    e.preventDefault();
    if (pw.length < 8) return setErr('Use at least 8 characters.');
    const { error } = await supabase.auth.updateUser({ password: pw });
    if (error) return setErr(error.message);
    router.push('/staff');
  }

  return (
    <>
      <h2>Set your password</h2>
      <div className="note">Choose a new password that you do not use anywhere else. Do not share it.</div>
      <form onSubmit={save}>
        <label>New password<input type="password" required minLength={8} autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} /></label>
        {err && <div className="err" role="alert">{err}</div>}
        <div><button className="pri" type="submit">Save password</button></div>
      </form>
    </>
  );
}
