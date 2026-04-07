export default function PageNavigation({ pages, activePage, onPageChange }) {
  return (
    <nav className="page-nav fade-in" aria-label="Assistant sections">
      {pages.map((page) => (
        <button
          key={page.id}
          type="button"
          className={`nav-pill ${activePage === page.id ? "is-active" : ""}`}
          onClick={() => onPageChange(page.id)}
        >
          {page.label}
        </button>
      ))}
    </nav>
  );
}
