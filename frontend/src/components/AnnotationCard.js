
import React from 'react';

const AnnotationCard = ({ annotation, onSwipe }) => {
  const { image, description } = annotation;

  return (
    <div className="annotation-card">
      <img src={image} alt="Surgery frame" />
      <p>{description}</p>
      <div className="swipe-buttons">
        <button onClick={() => onSwipe(true)}>Correct</button>
        <button onClick={() => onSwipe(false)}>Incorrect</button>
      </div>
    </div>
  );
};

export default AnnotationCard;
