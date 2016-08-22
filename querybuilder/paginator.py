from django.core.paginator import Paginator


class QuerybuilderPaginator(Paginator):

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.
        querybuilder expects the two numbers to be limit and offset. The limit will always be
        the per_page value and the offset will be the bottom number
        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = self.per_page
        return self._get_page(self.object_list[bottom:top], number, self)
