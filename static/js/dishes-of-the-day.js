(function () {
  var section = document.querySelector(".dishes-of-the-day");
  var list = document.getElementById("dotd-list");
  var dataEl = document.getElementById("dishes-data");
  if (!section || !list || !dataEl) return;

  var count = parseInt(section.getAttribute("data-count") || "6", 10);
  var root = section.getAttribute("data-root") || "/";
  if (root.charAt(root.length - 1) !== "/") root += "/";

  var recipes;
  try {
    recipes = JSON.parse(dataEl.textContent);
  } catch (e) {
    return;
  }
  if (!recipes.length) return;

  function todaySeed() {
    var d = new Date();
    var dd = String(d.getDate()).padStart(2, "0");
    var mm = String(d.getMonth() + 1).padStart(2, "0");
    var yy = String(d.getFullYear()).slice(-2);
    return dd + mm + yy + 12;
  }

  function score(slug, seed) {
    var data = new TextEncoder().encode(seed + ":" + slug);
    return crypto.subtle.digest("SHA-256", data).then(function (hash) {
      return Array.from(new Uint8Array(hash))
        .map(function (b) {
          return b.toString(16).padStart(2, "0");
        })
        .join("");
    });
  }

  function selectDishes(all, seed, n) {
    return Promise.all(
      all.map(function (recipe) {
        return score(recipe.slug, seed).then(function (s) {
          return { recipe: recipe, s: s };
        });
      })
    ).then(function (ranked) {
      ranked.sort(function (a, b) {
        return a.s < b.s ? -1 : a.s > b.s ? 1 : 0;
      });
      return ranked.slice(0, Math.min(n, ranked.length)).map(function (r) {
        return r.recipe;
      });
    });
  }

  function render(dishes) {
    list.innerHTML = "";
    dishes.forEach(function (dish) {
      var li = document.createElement("li");
      li.className = "dishes-of-the-day__item";

      var link = document.createElement("a");
      link.className = "dishes-of-the-day__link";
      link.href = root + dish.slug + "/";

      var name = document.createElement("span");
      name.className = "dishes-of-the-day__name";
      name.textContent = dish.title;
      link.appendChild(name);

      if (dish.description) {
        var desc = document.createElement("span");
        desc.className = "dishes-of-the-day__desc";
        desc.textContent = dish.description;
        link.appendChild(desc);
      }

      li.appendChild(link);
      list.appendChild(li);
    });
  }

  selectDishes(recipes, todaySeed(), count).then(render);
})();
