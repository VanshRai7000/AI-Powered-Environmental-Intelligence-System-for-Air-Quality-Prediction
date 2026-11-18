export default function Header() {
    return (
        <header className="h-16 border-b bg-white flex items-center justify-between px-6">
            <div>
                <h1 className="text-xl font-semibold">
                    Environmental Intelligence
                </h1>
            </div>

            <div>
                <span className="text-sm text-gray-600">
                    User Profile
                </span>
            </div>
        </header>
    );
}