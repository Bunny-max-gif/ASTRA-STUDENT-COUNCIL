'use client';
import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import ItemCard, { fd, inr } from '../components/ItemCard';

function SectionLabel({ children }) {
  return <div className="section-label"><span />{children}</div>;
}

function EmptyState({ children }) {
  return <div className="empty-state">{children}</div>;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboard() {
      const [items, budget, clubs] = await Promise.all([
        supabase.from('items').select('*').eq('status', 'approved').order('event_date', { ascending: true, nullsFirst: false }),
        supabase.from('club_budget').select('*').order('name'),
        supabase.from('clubs').select('id,name,kind').order('kind').order('name'),
      ]);
      const loadError = items.error || budget.error || clubs.error;
      if (loadError) {
        setError(loadError.message);
        return;
      }
      setError('');
      setData({ items: items.data, budget: budget.data, clubs: clubs.data });
    }

    loadDashboard();
  }, []);

  const clubs = data?.clubs ?? [];
  const items = data?.items ?? [];
  const clubNames = Object.fromEntries(clubs.map((club) => [club.id, club.name]));
  const today = new Date().toISOString().slice(0, 10);
  const upcoming = items.filter((item) => item.type === 'event' && item.event_date && item.event_date >= today);
  const projects = items.filter((item) => item.type === 'project');
  const announcements = items.filter((item) => item.type === 'announcement').slice(0, 3);
  const allocated = (data?.budget ?? []).reduce((total, club) => total + Number(club.allocated), 0);
  const spent = (data?.budget ?? []).reduce((total, club) => total + Number(club.spent), 0);

  return (
    <>
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <SectionLabel>ASTRA · STUDENT COUNCIL</SectionLabel>
          <h1 id="hero-title">Student life,<br /><span>engineered</span> together.</h1>
          <p className="hero-intro">
            A student-led community for big ideas, bold builds, and experiences that bring us closer.
            Find your people. Make something matter.
          </p>
          <div className="hero-actions">
            <a className="button button-gold" href="#community">Explore our community <span aria-hidden="true">↘</span></a>
            <a className="text-link" href="#whats-happening">See what&apos;s happening <span aria-hidden="true">→</span></a>
          </div>
          <div className="hero-note"><span className="live-dot" /> Built by students, for students</div>
        </div>

        <div className="hero-art" aria-label="ASTRA, a student community reaching beyond the ordinary">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="orbit orbit-three" />
          <div className="orbit-star star-one">✳</div>
          <div className="orbit-star star-two">✦</div>
          <div className="art-index">01 <span>/ COMMUNITY</span></div>
          <img className="hero-logo" src="/logo.png" alt="ASTRA" />
          <div className="art-caption"><span>Curiosity takes us further.</span><span>EST. FOR THE NEXT</span></div>
        </div>
        <div className="hero-bottomline"><span>IDEAS INTO ORBIT</span><span>STUDENT COUNCIL · ASTRA</span></div>
      </section>

      <section className="intro-strip" aria-label="About ASTRA">
        <p>More than a council.<br /><span>A launchpad for what&apos;s next.</span></p>
        <div className="strip-detail">From first sketches to final showcases, ASTRA brings the campus together to learn, create, and lead.</div>
        <a className="round-link" href="#community" aria-label="Explore the ASTRA community">↘</a>
      </section>

      <section className="content-section happenings" id="whats-happening">
        <div className="section-heading">
          <div>
            <SectionLabel>ON THE HORIZON</SectionLabel>
            <h2>Make room for <em>what&apos;s next.</em></h2>
          </div>
          <p>From events worth showing up for to projects worth seeing through.</p>
        </div>

        {error && <div className="note" role="status">Live updates are temporarily unavailable: {error}</div>}

        <div className="activity-grid">
          <article className="activity-panel events-panel">
            <div className="panel-top"><span>01 — UPCOMING</span><span className="panel-mark">↗</span></div>
            <h3>On the calendar</h3>
            <p className="panel-description">Good things happen when we get together.</p>
            {!data && !error ? <EmptyState>Loading council updates…</EmptyState> : upcoming.length ? (
              <div className="event-list">
                {upcoming.slice(0, 4).map((event) => (
                  <div className="event-row" key={event.id}>
                    <div className="event-date"><span>{fd(event.event_date).split(' ')[0]}</span>{fd(event.event_date).split(' ').slice(1).join(' ')}</div>
                    <div className="event-info"><strong>{event.title}</strong><span>{clubNames[event.club_id] || 'ASTRA'}</span></div>
                    <span className="event-arrow" aria-hidden="true">↗</span>
                  </div>
                ))}
              </div>
            ) : <EmptyState>No upcoming events just yet. Check back soon.</EmptyState>}
            <a className="panel-link" href="#community">Find your next thing <span>→</span></a>
          </article>

          <article className="activity-panel projects-panel" id="projects">
            <div className="panel-top"><span>02 — IN PROGRESS</span><span className="panel-mark">✳</span></div>
            <h3>Ideas in motion</h3>
            <p className="panel-description">A peek at what our teams are bringing to life.</p>
            {!data && !error ? <EmptyState>Loading council updates…</EmptyState> : projects.length ? (
              <div className="project-list">
                {projects.slice(0, 3).map((project) => (
                  <div className="project-row" key={project.id}>
                    <div className="project-row-heading"><strong>{project.title}</strong><span>{project.progress || 0}%</span></div>
                    <div className="project-track"><span style={{ width: `${project.progress || 0}%` }} /></div>
                    <span className="project-owner">{clubNames[project.club_id] || 'ASTRA'}</span>
                  </div>
                ))}
              </div>
            ) : <EmptyState>New projects are taking shape. Stay tuned.</EmptyState>}
            <a className="panel-link" href="#community">Meet the teams <span>→</span></a>
          </article>
        </div>
      </section>

      <section className="community-section" id="community">
        <div className="community-heading">
          <div>
            <SectionLabel>FIND YOUR PEOPLE</SectionLabel>
            <h2>There&apos;s a place<br />for <em>your kind of curious.</em></h2>
          </div>
          <p>Build, perform, compete, investigate, or make it all look good. However you show up, there&apos;s a team for you.</p>
        </div>
        <div className="community-grid">
          {clubs.length ? clubs.map((club, index) => (
            <article className="community-card" key={club.id}>
              <span className="community-number">{String(index + 1).padStart(2, '0')}</span>
              <span className="community-kind">{club.kind === 'club' ? 'CLUB' : 'WING'}</span>
              <h3>{club.name}</h3>
              <span className="community-arrow" aria-hidden="true">↗</span>
            </article>
          )) : (
            <>
              {['Aeromodeling', 'Rocketry', 'Astronomy', 'Cultural', 'Sports', 'Technical', 'Non-technical', 'Research', 'Disciplinary Committee', 'Media Team'].map((name, index) => (
                <article className="community-card" key={name}>
                  <span className="community-number">{String(index + 1).padStart(2, '0')}</span>
                  <span className="community-kind">{index < 3 ? 'CLUB' : 'WING'}</span>
                  <h3>{name}</h3>
                  <span className="community-arrow" aria-hidden="true">↗</span>
                </article>
              ))}
            </>
          )}
        </div>
      </section>

      <section className="transparency-section" id="budget">
        <div className="transparency-copy">
          <SectionLabel>GOOD IDEAS, OPEN BOOKS</SectionLabel>
          <h2>Built on trust.<br /><em>Made to make a difference.</em></h2>
          <p>Every contribution should go further. Explore how the council&apos;s resources are being put to work across our student community.</p>
          <div className="budget-total">
            <span>COUNCIL BUDGET USED</span>
            <strong>{allocated ? `${Math.round((spent / allocated) * 100)}%` : '—'}</strong>
            <span>{data ? `${inr(spent)} of ${inr(allocated)} allocated` : 'Updated by the student council'}</span>
          </div>
        </div>
        <div className="budget-list">
          <div className="budget-list-heading"><span>ALLOCATION BY TEAM</span><span>SPENT / TOTAL</span></div>
          {!data && !error ? <EmptyState>Loading budget updates…</EmptyState> : data?.budget.length ? data.budget.map((club) => {
            const percentage = club.allocated > 0 ? Math.round((club.spent / club.allocated) * 100) : 0;
            return (
              <div className="budget-row" key={club.id}>
                <div className="budget-row-heading"><strong>{club.name}</strong><span>{inr(club.spent)} <i>/ {inr(club.allocated)}</i></span></div>
                <div className="project-track"><span style={{ width: `${Math.min(percentage, 100)}%` }} /></div>
              </div>
            );
          }) : <EmptyState>Budget details will appear here as the council shares them.</EmptyState>}
        </div>
      </section>

      <section className="announcements-section" aria-labelledby="announcements-title">
        <div className="section-heading">
          <div><SectionLabel>FROM THE COUNCIL</SectionLabel><h2 id="announcements-title">A little <em>news.</em></h2></div>
          <p>Notes, news, and the occasional nudge from your student council.</p>
        </div>
        {!data && !error ? <EmptyState>Loading council updates…</EmptyState> : announcements.length ? (
          <div className="announcement-grid">
            {announcements.map((announcement) => (
              <ItemCard key={announcement.id} item={announcement} clubName={clubNames[announcement.club_id]} />
            ))}
          </div>
        ) : <EmptyState>No announcements yet. When there&apos;s news, you&apos;ll find it here.</EmptyState>}
      </section>

        <footer className="site-footer">
          <a className="footer-brand" href="/">
            <img src="/logo.png" alt="" />
            <span>ASTRA<small>STUDENT COUNCIL</small></span>
          </a>
          <p>Curiosity takes us further.<br />Made by students, for students.</p>
          <a className="footer-portal" href="/login">Council portal <span aria-hidden="true">↗</span></a>
          <span className="footer-credit">© {new Date().getFullYear()} ASTRA</span>
        </footer>
    </>
  );
}
