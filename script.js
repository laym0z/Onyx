// document.addEventListener("click", function(e) {
//     console.log("click!")
//     const folder = e.target.closest(".folder-name");
//     if (!folder) return;
//     console.log(folder)

//     const li = folder.parentElement;
//     console.log(li)
//     li.classList.toggle("open");
//     console.log(li)
//     console.log("click2")
// });


const STORAGE_KEY = "menu-open-folders";

function getState() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
}

function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function restoreMenuState() {

    const state = getState();

    document.querySelectorAll(".folder").forEach(folder => {

        const id = folder.dataset.folderid;

        if (state.includes(id)) {
            folder.classList.add("open");
        }

    });
}

document.addEventListener("click", function(e) {

    const folderName = e.target.closest(".folder-name");
    if (!folderName) return;

    const li = folderName.parentElement;
    // console.log(li)
    const id = li.dataset.folderid;
    // console.log(id)

    li.classList.toggle("open");

    let state = getState();

    if (li.classList.contains("open")) {
        if (!state.includes(id)) state.push(id);
    } else {
        state = state.filter(x => x !== id);
    }

    saveState(state);

});

document.addEventListener("DOMContentLoaded", restoreMenuState);