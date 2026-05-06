const hour = new Date().getHours();
let message = "";

if (hour < 12) {
    message = "Good Morning, Cyber Explorer!";
} else if (hour < 18) {
    message = "Good Afternoon, Cyber Defender!";
} else {
    message = "Good Evening, Night Watcher!";
}

console.log(message);
document.querySelector("h1").textContent = message;
