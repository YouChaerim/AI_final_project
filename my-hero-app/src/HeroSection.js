import React from 'react';
import './HeroSection.css';

const HeroSection = () => {
  return (
    <div className="hero-container">
      <video autoPlay loop muted className="background-video">
        <source src="https://www.w3schools.com/howto/rain.mp4" type="video/mp4" />
      </video>
      <div className="overlay"></div>
      <div className="hero-content">
        <h1 className="typing">未来へようこそ</h1>
        <p>AIによる革新。美しいデザイン。高い拡張性。</p>
        <button className="hero-button">今すぐ始める</button>
      </div>
    </div>
  );
};

export default HeroSection;

