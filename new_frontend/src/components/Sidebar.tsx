import { NavLink } from "react-router-dom";
import { Home, List, Briefcase, BarChart2 } from "lucide-react";

const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-800 p-4">
      <h1 className="text-2xl font-bold mb-8">Zerodha Dashboard</h1>
      <nav>
        <ul>
          <li>
            <NavLink to="/" className="flex items-center p-2 rounded-md hover:bg-gray-700">
              <Home className="mr-2" />
              Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/orders" className="flex items-center p-2 rounded-md hover:bg-gray-700">
              <List className="mr-2" />
              Orders
            </NavLink>
          </li>
          <li>
            <NavLink to="/holdings" className="flex items-center p-2 rounded-md hover:bg-gray-700">
              <Briefcase className="mr-2" />
              Holdings
            </NavLink>
          </li>
          <li>
            <NavLink to="/watchlist" className="flex items-center p-2 rounded-md hover:bg-gray-700">
              <BarChart2 className="mr-2" />
              Watchlist
            </NavLink>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
