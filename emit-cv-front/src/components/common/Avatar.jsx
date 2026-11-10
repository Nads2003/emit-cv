export default function Avatar({ user, size = 44 }) {
  if (user?.photo) {
    return (
      <img
        src={user.photo}
        alt=""
        style={{ width: size, height: size }}
        className="shrink-0 rounded-full object-cover"
      />
    );
  }
  return (
    <span
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      className="flex shrink-0 items-center justify-center rounded-full bg-brand font-bold text-white"
    >
      {(user?.nom ?? "D").charAt(0).toUpperCase()}
    </span>
  );
}