import logo from '../assets/logo.png';

export function Header() {
  return (
    <header className="site-header">
      <img src={logo} alt="Logo da empresa" className="site-header__logo" />
      <div className="site-header__accent" />
    </header>
  );
}
