import  {useState} from 'react';
import axios from 'axios';

import './Login.css'

const Login = () => {
  const [credentials,setCredentials]=useState(
    {
      client_id:"",
      client_secret:"",
    }
  );
  const [error, setError] = useState(null);


  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null); // Clear previous errors

    try {
      //const response = await axios.post("http://localhost:8080/login", credentials);

      const response = await axios.post(
        "http://localhost:8080/login",
        credentials,
        {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      console.log(response.data);
      alert("Login successful!");

      if (response.data.status === "success") {
        window.location.href = "http://localhost:8080/auth";
      } else {
        setError(response.data.error || "Invalid credentials");
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err.response?.data?.error || "An error occurred while logging in");
    }
  };



  return (
    <div style={{ textAlign: "center", marginTop: "20px" }}>
    <section className="align_center form_page">
      <form className='credentials_form' onSubmit={handleSubmit}>
        <h2 className="form_title">App Credentials</h2>
        <div className="form_inputs">
          <div>
            <label className="form_label" htmlFor="client_id" >Client ID:</label>
            <input 
              id='client_id' 
              type='text' 
              className='form_text_input' 
              placeholder='Your spotify client id' 
              required="required"
              onChange={e => setCredentials({...credentials,client_id:e.target.value})}
              value={credentials.client_id} 
            />

          </div>
          <div>
            <label className="form_label" htmlFor="client_secret" >Client secret:</label>
            <input 
              id='client_secret' 
              type='text' 
              className='form_text_input' 
              placeholder='Enter your spotify client secret'
              required="required"
              onChange={e => setCredentials({...credentials,client_secret:e.target.value})}
              value={credentials.client_secret}
            />

          </div>
          <button type='submit' className='classic_button form_submit'>Submit</button>
        </div>
        {error && <p className="form_error" style={{ color: "red" }}>{error}</p>}
      </form>

    </section>
  </div>
  )
}

export default Login