import React from 'react';
import { NavLink } from 'react-router-dom';

// This component can be included by Layout to inject extra nav links without breaking existing structure
const SidebarLinksInjection = () => {
  return (
    <>
      <NavLink to="/live" className={({isActive}) => `block px-3 py-2 rounded-md ${isActive? 'bg-blue-600 text-white':'text-gray-800 hover:bg-gray-100'}`}>Живой разговор</NavLink>
    </>
  );
};

export default SidebarLinksInjection;