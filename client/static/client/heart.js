const heart = document.querySelector(".heart");
const animationHeart = document.querySelector(".animation-heart");


heart.addEventListener('click', () => {
	animationHeart.classList.add('animation');
	heart.classList.add('fill-color');
})

animationHeart.addEventListener('click', () =>{
	animationHeart.classList.remove('animation');
	heart.classList.remove('fill-color');
})