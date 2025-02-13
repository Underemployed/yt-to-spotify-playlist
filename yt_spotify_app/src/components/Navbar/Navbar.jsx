import  'react';
//import Logo from '../Logo/Logo'
import './Navbar.css';
import { NavLink } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className='navbar'>
        <div className="navbar-brand">

        </div>
        <div className='navbar-links'>
            <NavLink to ='/'>Home</NavLink>
            <NavLink to ='/about'>About</NavLink>
            <NavLink to ='/credits'>Credits</NavLink>
            <NavLink to ='/profile'>Profile</NavLink>
            <NavLink to ='/dashboard'>TestDash</NavLink>
        </div>
    </nav>
  )
}

export default Navbar
