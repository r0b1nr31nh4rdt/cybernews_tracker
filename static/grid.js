function initGrid() {
    document.querySelectorAll(".module").forEach(module => {
        module.style.touchAction = "none";
        module.querySelector(".module__header").style.touchAction = "none";

        interact(module)
            .draggable({
                allowFrom: ".module__header",
                listeners: {
                    move(e) {
                        const el = e.target;
                        const row = el.closest(".grid-row");
                        if (!row) return;

                        el.style.visibility = "hidden";
                        const elementUnder = document.elementFromPoint(e.clientX, e.clientY);
                        el.style.visibility = "";

                        if (!elementUnder) return;
                        const targetModule = elementUnder.closest(".module");

                        if (targetModule && targetModule !== el && row.contains(targetModule)) {
                            const siblings = [...row.querySelectorAll(".module")];
                            const elIdx = siblings.indexOf(el);
                            const targetIdx = siblings.indexOf(targetModule);

                            if (elIdx < targetIdx) {
                                row.insertBefore(targetModule, el);
                            } else {
                                row.insertBefore(el, targetModule);
                            }
                        }
                    },
                    end(e) {
                        console.log("drag end — neue Reihenfolge gespeichert");
                    }
                }
            })
            .resizable({
                edges: { right: true, bottom: true, bottomRight: true },
                listeners: {
                    move(e) {
                        e.target.style.flexBasis = e.rect.width + "px";
                        e.target.style.height = e.rect.height + "px";
                    }
                },
                modifiers: [
                    interact.modifiers.restrictSize({ min: { width: 180, height: 150 } })
                ]
            });
    });
}

document.addEventListener("DOMContentLoaded", initGrid);

window.CyberGrid = { init: () => {} };
