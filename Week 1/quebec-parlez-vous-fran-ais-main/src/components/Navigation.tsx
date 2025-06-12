
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { 
  BookOpen, 
  Activity, 
  Settings as SettingsIcon 
} from "lucide-react";

const navigationItems = [
  { name: "Dashboard", href: "/dashboard", icon: BookOpen },
  { name: "Study Activities", href: "/study-activities", icon: Activity },
  { name: "Words", href: "/words", icon: BookOpen },
  { name: "Word Groups", href: "/groups", icon: BookOpen },
  { name: "Sessions", href: "/sessions", icon: Activity },
  { name: "Settings", href: "/settings", icon: SettingsIcon },
];

export function Navigation() {
  const location = useLocation();

  return (
    <nav className="bg-white shadow-lg border-b border-blue-100">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">QF</span>
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Québec Français
              </h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-blue-100 text-blue-700 shadow-sm"
                      : "text-gray-600 hover:text-blue-600 hover:bg-blue-50"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
