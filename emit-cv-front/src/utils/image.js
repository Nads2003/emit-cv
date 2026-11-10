/**
 * Recadre l'image en carré (centré) et la réduit à `size` px.
 * Renvoie { blob, preview } : blob pour l'envoi au serveur, preview (data URL) pour l'affichage.
 */
export const resizeImage = (file, size = 256) =>
  new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      const side = Math.min(img.width, img.height);
      const sx = (img.width - side) / 2;
      const sy = (img.height - side) / 2;

      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = size;
      canvas.getContext("2d").drawImage(img, sx, sy, side, side, 0, 0, size, size);
      URL.revokeObjectURL(url);

      canvas.toBlob(
        (blob) =>
          blob
            ? resolve({ blob, preview: canvas.toDataURL("image/jpeg", 0.85) })
            : reject(new Error("blob")),
        "image/jpeg",
        0.85,
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("image"));
    };
    img.src = url;
  });