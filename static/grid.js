function initGrid() {
    document.querySelectorAll(".module").forEach(module => {
        module.style.touchAction = "none";
        module.querySelector(".module__header").style.touchAction = "none";

        const handleLeft  = document.createElement("div");
        const handleRight = document.createElement("div");
        handleLeft.className  = "resize-handle resize-handle--left";
        handleRight.className = "resize-handle resize-handle--right";
        module.appendChild(handleLeft);
        module.appendChild(handleRight);

        interact(module)
            .draggable({
                allowFrom: ".module__header",
                listeners: {
                    move(e) {
                        const el = e.target;

                        el.style.visibility = "hidden";
                        const elementUnder = document.elementFromPoint(e.clientX, e.clientY);
                        el.style.visibility = "";

                        if (!elementUnder) return;

                        const targetRow = elementUnder.closest(".grid-row");
                        if (!targetRow) return;

                        const targetModule = elementUnder.closest(".module");

                        if (targetModule && targetModule !== el) {
                            const targetRect = targetModule.getBoundingClientRect();
                            const insertAfter = e.clientX > targetRect.left + targetRect.width / 2;

                            if (insertAfter) {
                                targetRow.insertBefore(el, targetModule.nextSibling);
                            } else {
                                targetRow.insertBefore(el, targetModule);
                            }
                        } else if (!targetModule && targetRow !== el.closest(".grid-row")) {
                            targetRow.appendChild(el);
                        }
                    },
                    end(e) {
                        document.querySelectorAll(".grid-row").forEach(row => {
                            const order = [...row.querySelectorAll(".module")]
                                .map(m => m.dataset.id);
                            localStorage.setItem("grid-order-" + row.id, JSON.stringify(order));
                        });
                        if (window.CyberMap) window.CyberMap.resize();
                    }
                }
            })
            .resizable({
                edges: { right: true, bottom: true, bottomRight: true, left: true },
                listeners: {
                    start(e) {
                        const el = e.target;
                        el.setAttribute("data-resizing", "true");
                        const computed = el.getBoundingClientRect();
                        el.style.flexGrow   = "0";
                        el.style.flexShrink = "0";
                        el.style.flexBasis  = computed.width + "px";
                        el.style.height     = computed.height + "px";
                    },
                    move(e) {
                        const el = e.target;
                        el.style.flexBasis = e.rect.width + "px";
                        el.style.height    = e.rect.height + "px";
                    },
                    end(e) {
                        e.target.removeAttribute("data-resizing");
                        saveModuleSizes();
                        notifyModulesResized();
                    }
                },
                modifiers: [
                    interact.modifiers.restrictSize({ min: { width: 180, height: 150 } })
                ]
            });
    });

    document.addEventListener("mouseup", () => {
        document.querySelectorAll(".module").forEach(el => {
            if (el.getAttribute("data-resizing") === "true") {
                el.removeAttribute("data-resizing");
                saveModuleSizes();
                notifyModulesResized();
            }
        });
    });
}

function saveModuleSizes() {
    const sizes = {};
    document.querySelectorAll(".module[data-id]").forEach(el => {
        const entry = {};
        if (el.style.flexBasis) entry.width  = el.style.flexBasis;
        if (el.style.height)    entry.height = el.style.height;
        if (Object.keys(entry).length) sizes[el.dataset.id] = entry;
    });
    localStorage.setItem("grid-sizes", JSON.stringify(sizes));
}

function notifyModulesResized() {
    if (window.CyberMap) window.CyberMap.resize();

    const video = document.getElementById("stream-player");
    if (video) {
        const body = video.closest(".module__body");
        if (body) video.style.height = body.clientHeight - 40 + "px";
    }
}

function resetGrid() {
    localStorage.removeItem("grid-sizes");
    localStorage.removeItem("grid-order-grid-top");
    localStorage.removeItem("grid-order-grid-bottom");
    document.querySelectorAll(".module").forEach(el => {
        el.style.flexBasis  = "";
        el.style.flexGrow   = "";
        el.style.flexShrink = "";
        el.style.height     = "";
    });
    console.log("Grid zurückgesetzt");
}

function initGridComplete() {
    interact.pointerMoveTolerance(1);
    initGrid();
}

document.addEventListener("DOMContentLoaded", initGridComplete);

window.CyberGrid = { init: () => {}, reset: resetGrid };

