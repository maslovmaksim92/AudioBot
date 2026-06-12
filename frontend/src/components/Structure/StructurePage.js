import React from 'react';
import {
  Network, User, MessageSquare, Bot, Server, Database, Globe, Mic, Cpu,
  ArrowRight, ArrowDown, ArrowLeftRight, ClipboardList, FlaskConical, ShieldCheck,
  Rocket, Activity, Search, FileText, BarChart3, Lock, Workflow, CheckCircle2,
  Clock, AlertTriangle, XCircle, Loader2, HelpCircle
} from 'lucide-react';

const Node = ({ icon: Icon, title, subtitle, accent = 'sky', wide = false }) => {
  const ring = {
    sky: 'border-sky-500/40 bg-sky-500/10 text-sky-100',
    emerald: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-100',
    violet: 'border-violet-500/40 bg-violet-500/10 text-violet-100',
    amber: 'border-amber-500/40 bg-amber-500/10 text-amber-100',
    slate: 'border-slate-500/40 bg-slate-500/10 text-slate-100',
    rose: 'border-rose-500/40 bg-rose-500/10 text-rose-100',
  }[accent] || 'border-slate-500/40 bg-slate-500/10 text-slate-100';
  return (
    <div className={`rounded-xl border ${ring} px-4 py-3 shadow-md backdrop-blur ${wide ? 'flex-1' : ''}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5 shrink-0" />
        <div className="font-semibold leading-tight">{title}</div>
      </div>
      {subtitle && <div className="text-xs opacity-80 mt-1 leading-snug">{subtitle}</div>}
    </div>
  );
};

const Arrow = ({ dir = 'right', label }) => {
  const Icon = dir === 'right' ? ArrowRight : dir === 'down' ? ArrowDown : ArrowLeftRight;
  return (
    <div className="flex flex-col items-center justify-center text-slate-400 px-1 py-1 select-none">
      <Icon className="w-5 h-5" />
      {label && <span className="text-[10px] mt-0.5 whitespace-nowrap">{label}</span>}
    </div>
  );
};

// Responsive arrow: shows horizontal on md+, vertical on mobile
const FlowArrow = ({ label }) => (
  <>
    <div className="hidden md:flex"><Arrow dir="right" label={label} /></div>
    <div className="md:hidden flex"><Arrow dir="down" label={label} /></div>
  </>
);

const BiArrow = ({ label }) => (
  <>
    <div className="hidden md:flex"><Arrow dir="lr" label={label} /></div>
    <div className="md:hidden flex"><Arrow dir="down" label={label} /></div>
  </>
);

const SectionCard = ({ title, subtitle, children }) => (
  <section className="rounded-2xl border border-slate-700/60 bg-slate-900/60 p-5 md:p-6 shadow-lg">
    <header className="mb-4">
      <h2 className="text-lg md:text-xl font-semibold text-slate-100">{title}</h2>
      {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
    </header>
    {children}
  </section>
);

const AgentCard = ({ icon: Icon, name, role, bullets, accent = 'sky', soon = false }) => {
  const ring = {
    sky: 'border-sky-500/40 bg-sky-500/5',
    emerald: 'border-emerald-500/40 bg-emerald-500/5',
    violet: 'border-violet-500/40 bg-violet-500/5',
    amber: 'border-amber-500/40 bg-amber-500/5',
    slate: 'border-slate-500/40 bg-slate-500/5',
    rose: 'border-rose-500/40 bg-rose-500/5',
  }[accent] || 'border-slate-500/40 bg-slate-500/5';
  return (
    <div className={`rounded-xl border ${ring} p-4 flex flex-col gap-2 min-w-0`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Icon className="w-5 h-5 text-slate-200 shrink-0" />
          <div className="min-w-0">
            <div className="text-slate-100 font-semibold truncate">{name}</div>
            {role && <div className="text-xs text-slate-400 truncate">{role}</div>}
          </div>
        </div>
        {soon && (
          <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/40 text-amber-200 shrink-0">
            скоро
          </span>
        )}
      </div>
      <ul className="text-xs text-slate-300/90 space-y-1 mt-1 list-disc list-inside">
        {bullets.map((b, i) => <li key={i}>{b}</li>)}
      </ul>
    </div>
  );
};

const StatusBadge = ({ icon: Icon, label, color }) => (
  <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs ${color}`}>
    <Icon className="w-3.5 h-3.5" />
    <span className="font-medium">{label}</span>
  </div>
);

export default function StructurePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 text-slate-100 p-6 md:p-8 shadow-lg border border-slate-700/60">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-sky-500/15 border border-sky-500/30">
            <Network className="w-6 h-6 text-sky-300" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold">Структура системы</h1>
            <p className="text-sm md:text-base text-slate-400 mt-1">
              Карта взаимодействия владельца, MAX-мессенджера, агента Hermes, ВПС и фабрики разработки Claude Code.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-6 text-slate-100">
        {/* ============ Секция 1. ОБЩАЯ АРХИТЕКТУРА ============ */}
        <SectionCard
          title="1. Общая архитектура"
          subtitle="Кто с кем взаимодействует и где что живёт"
        >
          {/* Верхний поток: Владелец ⇄ MAX → Hermes → ВПС */}
          <div className="flex flex-col md:flex-row md:items-stretch gap-3">
            <Node icon={User} title="Владелец" subtitle="Ставит задачи, утверждает планы и деплой" accent="emerald" wide />
            <BiArrow label="чат" />
            <Node icon={MessageSquare} title="MAX-мессенджер" subtitle="Канал общения с агентом Hermes" accent="sky" wide />
            <FlowArrow />
            <Node icon={Bot} title="Hermes" subtitle="Бот в MAX · мост /opt/hermes-max-bridge" accent="violet" wide />
            <FlowArrow />
            <Node icon={Server} title="ВПС" subtitle="Хост приложения и фабрики разработки" accent="slate" wide />
          </div>

          {/* Внутренности ВПС */}
          <div className="mt-5 rounded-xl border border-slate-700/60 bg-slate-800/40 p-4">
            <div className="text-xs uppercase tracking-wider text-slate-400 mb-3">Что крутится на ВПС</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* audiobot */}
              <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Globe className="w-5 h-5 text-sky-300" />
                  <div>
                    <div className="text-sky-100 font-semibold">audiobot</div>
                    <div className="text-xs text-slate-400">этот дашборд · ai.vd40.ru</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Node icon={Cpu} title="FastAPI" subtitle="backend" accent="sky" />
                  <Node icon={Database} title="Postgres" subtitle="БД" accent="emerald" />
                  <Node icon={Globe} title="React" subtitle="frontend" accent="violet" />
                  <Node icon={Mic} title="voice_web" subtitle="голос · :8123" accent="amber" />
                </div>
              </div>

              {/* Фабрика */}
              <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Workflow className="w-5 h-5 text-violet-300" />
                  <div>
                    <div className="text-violet-100 font-semibold">Фабрика разработки Claude Code</div>
                    <div className="text-xs text-slate-400">Оркестратор + дев/QA-агенты + (скоро) Deploy/Ops/…</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <Node icon={ClipboardList} title="Orchestrator" accent="sky" />
                  <Node icon={FlaskConical} title="Dev" accent="emerald" />
                  <Node icon={ShieldCheck} title="QA" accent="violet" />
                </div>
              </div>
            </div>
          </div>
        </SectionCard>

        {/* ============ Секция 2. АГЕНТЫ ФАБРИКИ ============ */}
        <SectionCard
          title="2. Агенты фабрики разработки"
          subtitle="Действующие сегодня и плановые (с пометкой «скоро»)"
        >
          <div className="text-xs uppercase tracking-wider text-slate-400 mb-3">Активные · конвейер задачи</div>
          <div className="flex flex-col md:flex-row md:items-stretch gap-3">
            <AgentCard
              icon={ClipboardList}
              name="Orchestrator"
              role="orchestrate"
              accent="sky"
              bullets={[
                'Декомпозиция задачи и маршрутизация',
                'Контроль конвейера и таймауты',
                'Таймаут: 90 мин',
                'Журнал: /var/log/orchestrator',
              ]}
            />
            <FlowArrow />
            <AgentCard
              icon={FlaskConical}
              name="Dev-агент"
              role="devtask"
              accent="emerald"
              bullets={[
                'TDD-конвейер: план → тесты → код → ревью',
                'Субагенты: architect, test-writer, implementer, reviewer, security',
                'Worktree-изоляция',
                'Таймаут: 45 мин · лимит: 5 циклов',
              ]}
            />
            <FlowArrow />
            <AgentCard
              icon={ShieldCheck}
              name="QA-агент"
              role="qa-agent"
              accent="violet"
              bullets={[
                'Независимая приёмка задачи',
                'Перепрогон тестов, Playwright desktop+mobile',
                'НЕ правит код',
                'Таймаут: 30 мин',
              ]}
            />
          </div>

          <div className="text-xs uppercase tracking-wider text-slate-400 mt-6 mb-3">Плановые агенты</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <AgentCard icon={Rocket} name="Deploy" role="release" accent="amber" soon
              bullets={['Деплой после явного «ДА»', 'Автооткат при сбое']} />
            <AgentCard icon={Activity} name="Ops" role="ops-watch" accent="amber" soon
              bullets={['Мониторинг прода 24/7', 'Алёрты и автодиагностика']} />
            <AgentCard icon={Search} name="Research" role="research" accent="amber" soon
              bullets={['Исследования рынка', 'Сбор и сводка источников']} />
            <AgentCard icon={FileText} name="Content" role="content" accent="amber" soon
              bullets={['Коммерческие предложения', 'Тексты и рассылки']} />
            <AgentCard icon={BarChart3} name="Data" role="analytics" accent="amber" soon
              bullets={['Аналитика по БД', 'Витрины и регулярные отчёты']} />
            <AgentCard icon={Lock} name="Security" role="audit" accent="amber" soon
              bullets={['Еженедельный аудит', 'Секреты, зависимости, доступы']} />
          </div>
        </SectionCard>

        {/* ============ Секция 3. БИЗНЕС-ПРОЦЕСС ============ */}
        <SectionCard
          title="3. Бизнес-процесс задачи"
          subtitle="От постановки в MAX до прод-деплоя"
        >
          <div className="flex flex-col md:flex-row md:flex-wrap md:items-stretch gap-3">
            <Node icon={User} title="Владелец" subtitle="ставит задачу" accent="emerald" />
            <FlowArrow />
            <Node icon={MessageSquare} title="MAX" subtitle="сообщение" accent="sky" />
            <FlowArrow />
            <Node icon={Bot} title="Hermes" subtitle="приём задачи" accent="violet" />
            <FlowArrow />
            <Node icon={ClipboardList} title="orchestrate" subtitle="декомпозиция" accent="sky" />
            <FlowArrow />
            <Node icon={FileText} title="План" subtitle="подтверждение владельца" accent="amber" />
            <FlowArrow />
            <Node icon={FlaskConical} title="Разработка" subtitle="в worktree (TDD)" accent="emerald" />
            <FlowArrow />
            <Node icon={ShieldCheck} title="QA-приёмка" subtitle="PASS / FAIL" accent="violet" />
            <FlowArrow label="PASS" />
            <Node icon={CheckCircle2} title="Merge" subtitle="подтверждение владельца" accent="emerald" />
            <FlowArrow />
            <Node icon={Rocket} title="Deployment package" subtitle="готовый артефакт" accent="amber" />
            <FlowArrow label="«ДА»" />
            <Node icon={Server} title="Прод" subtitle="ai.vd40.ru" accent="slate" />
          </div>

          {/* Легенда статусов */}
          <div className="mt-6 rounded-xl border border-slate-700/60 bg-slate-800/40 p-4">
            <div className="text-xs uppercase tracking-wider text-slate-400 mb-3">Легенда статусов конвейера</div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge icon={CheckCircle2} label="DONE" color="border-emerald-500/40 bg-emerald-500/10 text-emerald-200" />
              <StatusBadge icon={ShieldCheck} label="PASS" color="border-emerald-500/40 bg-emerald-500/10 text-emerald-200" />
              <StatusBadge icon={HelpCircle} label="NEEDS-CONFIRM" color="border-amber-500/40 bg-amber-500/10 text-amber-200" />
              <StatusBadge icon={Loader2} label="BUSY" color="border-sky-500/40 bg-sky-500/10 text-sky-200" />
              <StatusBadge icon={AlertTriangle} label="BLOCKED" color="border-rose-500/40 bg-rose-500/10 text-rose-200" />
              <StatusBadge icon={XCircle} label="FAIL" color="border-rose-500/40 bg-rose-500/10 text-rose-200" />
              <StatusBadge icon={Clock} label="ABORTED" color="border-slate-500/40 bg-slate-500/10 text-slate-200" />
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
