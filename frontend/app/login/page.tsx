export default function LoginPage() {
  return (
    <form>
      <h1>Login</h1>
      <input aria-label="email" type="email" required />
      <input aria-label="password" type="password" required />
      <button type="submit">Login</button>
    </form>
  )
}
