import React from 'react';
//import Logo from '../Logo/Logo'
import './Navbar.css';

const Navbar = () => {
  return (
    <nav className='navbar'>
        <div className="navbar-brand">

        </div>
        <div className='navbar-links'>
            <a href='/'>Home</a>
            <a href='/about'>About</a>
            <a href='/credits'>Credits</a>
            <a href='/profile'>Profile</a>
        </div>
    </nav>
  )
}

export default Navbar
