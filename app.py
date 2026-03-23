from flask import Flask, Response

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Pro 3D Viewer</title>
  <style>
    body { margin: 0; overflow: hidden; font-family: Arial; }
    #panel {
      position: absolute;
      top: 10px;
      left: 10px;
      background: #111;
      color: white;
      padding: 10px;
      border-radius: 8px;
      width: 250px;
    }
  </style>
</head>
<body>

<div id="panel">
  <h3>3D Viewer</h3>
  <input type="file" id="file" />
  <p id="info">Click on model</p>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.158/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.158/examples/js/loaders/STLLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.158/examples/js/controls/OrbitControls.js"></script>

<script>
let scene = new THREE.Scene();
let camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
let renderer = new THREE.WebGLRenderer();

renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

let controls = new THREE.OrbitControls(camera, renderer.domElement);

camera.position.set(0, 0, 100);

let light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(10,10,10);
scene.add(light);

let mesh = null;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();

function animate(){
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();

// LOAD FILE
document.getElementById("file").onchange = (e) => {
  let file = e.target.files[0];
  let url = URL.createObjectURL(file);

  let loader = new THREE.STLLoader();
  loader.load(url, (geometry) => {

    scene.clear();
    scene.add(light);

    let material = new THREE.MeshStandardMaterial({
      color: 0x00ff88,
      metalness: 0.3,
      roughness: 0.5
    });

    mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);
  });
};

// CLICK SELECT
window.addEventListener("click", (event) => {
  if (!mesh) return;

  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);

  let intersects = raycaster.intersectObject(mesh);

  if (intersects.length > 0) {
    let point = intersects[0].point;

    document.getElementById("info").innerText =
      "Clicked at: " + point.x.toFixed(2) + ", " +
      point.y.toFixed(2) + ", " +
      point.z.toFixed(2);

    // highlight
    mesh.material.color.set(0xff0000);
  }
});
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return Response(HTML, mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True)