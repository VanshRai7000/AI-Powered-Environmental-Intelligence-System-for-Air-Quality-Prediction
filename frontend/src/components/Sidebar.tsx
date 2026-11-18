interface SidebarProps {
    activeSection: string;
    onSelectSection: (sectionId: string) => void;
}

const NAV_ITEMS = [
    { id: "overview", label: "Dashboard", icon: "📊" },
    { id: "air-quality", label: "Air Quality & Weather", icon: "🌬️" },
    { id: "pollution-map", label: "Pollution Map", icon: "🗺️" },
    { id: "analytics", label: "Historical Analytics", icon: "📈" },
];

export default function Sidebar({ activeSection, onSelectSection }: SidebarProps) {
    return (
        <aside className="hidden md:flex flex-col w-60 min-h-screen border-r border-slate-200 bg-white p-4 shrink-0">
            <div className="px-3 py-2 mb-4">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    Navigation
                </p>
            </div>
            <nav className="space-y-1.5">
                {NAV_ITEMS.map((item) => {
                    const isActive = activeSection === item.id;
                    return (
                        <button
                            key={item.id}
                            type="button"
                            onClick={() => onSelectSection(item.id)}
                            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2.5 transition-colors cursor-pointer ${
                                isActive
                                    ? "bg-slate-900 text-white shadow-sm"
                                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                            }`}
                        >
                            <span>{item.icon}</span>
                            <span>{item.label}</span>
                        </button>
                    );
                })}
            </nav>
        </aside>
    );
}
