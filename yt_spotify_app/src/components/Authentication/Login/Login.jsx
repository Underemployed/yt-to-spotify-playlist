import React, {useState} from 'react';

import './Login.css'

const Login = () => {
  const [credentials,setCredentials]=useState(
    {
      client_id:"",
      client_secret:"",
    }
  );
  

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(credentials);
  }

    

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
              onChange={e => setCredentials({...credentials,client_secret:e.target.value})}
              value={credentials.client_secret}
            />
            
          </div>
          <button type='submit' className='classic_button form_submit'>Submit</button>
        </div>

      </form>
    </section>
  </div>
  )
}

export default Login

