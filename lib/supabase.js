import { createClient } from '@supabase/supabase-js';

// True when the person arrived by clicking an invite or password-reset email link.
export const arrivedViaLink =
  typeof window !== 'undefined' && /type=(invite|recovery)/.test(window.location.hash);

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);
