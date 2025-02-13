import "react";


import "./App.css";
import Navbar from "./components/Navbar/Navbar";
import { Route ,Routes } from "react-router-dom";
import Home from "./components/Home/Home";
import About from "./components/About/About";
import Credits from "./components/Credits/Credits";
import Login from "./components/Authentication/Login/Login";
import NotFound from "./components/NotFound/NotFound";
import Dash from "./components/Dash/Dash";
//import Routing from "./components/Routing/Routing";

const App = () => {
    return (
        <div className='app'>
            <Navbar />
            <main className="app_main">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/about" element={<About />} />
                <Route path="/credits" element={<Credits />} />
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="*" element={<NotFound />} />
                <Route path="/dashboard" element={<Dash />} />
              </Routes>
            </main>
        </div>
    );
};

export default App;
