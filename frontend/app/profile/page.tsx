export default function ProfilePage() {
  return (
    <section>
      <h1>Profile</h1>
      <textarea aria-label="bio" placeholder="Bio" />
      <input aria-label="tags" placeholder="expertise tags" />
      <input aria-label="links" placeholder="social links" />
      <button>Save</button>
    </section>
  )
}
