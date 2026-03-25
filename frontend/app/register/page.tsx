export default function RegisterPage() {
  return (
    <form>
      <h1>Register</h1>
      <input aria-label="email" type="email" required />
      <input aria-label="username" required />
      <input aria-label="password" type="password" required />
      <button type="submit">Create account</button>
    </form>
  )
}
