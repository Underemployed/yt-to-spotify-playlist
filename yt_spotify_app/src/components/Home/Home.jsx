import {useNavigate } from "react-router-dom";
import "./Home.css";
const Home = () => {

  const navigate = useNavigate();

  const handleGetStartedClick = () => {
    navigate("/login");
  };
  return (
    <div className="home-wrapper">
   
      <div className='spotify-container'>
        <h2>Youtube to spotify porter</h2>      
        <button className='get-started-btn' onClick={handleGetStartedClick}> Get Started
        </button>
      </div>  
        
    </div>
  )
}

export default Home