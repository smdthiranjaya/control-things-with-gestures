// Add this debounce function near the top of your script section
// Right after the createApp call
function debounce(func, wait) {
  let timeout;
  return function() {
    const context = this;
    const args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}

// Then update this part later in your code:
// Replace your existing updateSettings function with this debounced version
const updateSettings = debounce(async () => {
  try {
    console.log("Applying settings changes...");
    await axios.post("/api/settings", settings.value);
    setTimeout(() => {
      updateVideoFeedUrl();
    }, 1000);
  } catch (error) {
    console.error("Error updating settings:", error);
  }
}, 500);  // 500ms debounce time